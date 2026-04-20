from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import secrets
import os

from database import engine, get_db, Base
import models
import bcrypt
from jose import JWTError, jwt

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GroupSync")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "groupsync-super-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# --- Auth Helpers ---
# Using bcrypt directly to avoid passlib version compatibility issues

def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit, truncate to be safe
    password_bytes = password[:72].encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    plain_bytes = plain[:72].encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    user = db.query(models.User).filter(models.User.username == username).first()
    return user

def require_user(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=302, detail="Redirect", headers={"Location": "/login"})
    return user

# --- Pages ---

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    token = create_access_token({"sub": user.username})
    # Check for pending invite
    pending_invite = request.cookies.get("pending_invite")
    redirect_url = "/dashboard"
    if pending_invite:
        group = db.query(models.Group).filter(models.Group.invite_code == pending_invite).first()
        if group:
            existing = db.query(models.GroupMember).filter(
                models.GroupMember.user_id == user.id,
                models.GroupMember.group_id == group.id
            ).first()
            if not existing:
                member = models.GroupMember(user_id=user.id, group_id=group.id)
                db.add(member)
                db.commit()
            redirect_url = f"/chat/{group.id}"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie("access_token", token, httponly=True, max_age=86400)
    response.delete_cookie("pending_invite")
    return response

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username or email already taken"})
    user = models.User(
        username=username,
        email=email,
        hashed_password=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.username})
    # Check for pending invite
    pending_invite = request.cookies.get("pending_invite")
    redirect_url = "/dashboard"
    if pending_invite:
        group = db.query(models.Group).filter(models.Group.invite_code == pending_invite).first()
        if group:
            member = models.GroupMember(user_id=user.id, group_id=group.id)
            db.add(member)
            db.commit()
            redirect_url = f"/chat/{group.id}"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie("access_token", token, httponly=True, max_age=86400)
    response.delete_cookie("pending_invite")
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    memberships = db.query(models.GroupMember).filter(models.GroupMember.user_id == user.id).all()
    groups = [m.group for m in memberships]
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "groups": groups})

@app.get("/chat/{group_id}", response_class=HTMLResponse)
def chat_page(group_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    member = db.query(models.GroupMember).filter(
        models.GroupMember.user_id == user.id,
        models.GroupMember.group_id == group_id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    members = db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).all()
    messages = db.query(models.Message).filter(models.Message.group_id == group_id).order_by(models.Message.created_at).all()
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user": user,
        "group": group,
        "members": members,
        "messages": messages
    })

# --- API Endpoints ---

@app.post("/api/groups/create")
def create_group(request: Request, name: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    existing = db.query(models.Group).filter(models.Group.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group name already taken")
    invite_code = secrets.token_urlsafe(8)
    group = models.Group(
        name=name,
        hashed_password=hash_password(password),
        invite_code=invite_code,
        created_by=user.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    member = models.GroupMember(user_id=user.id, group_id=group.id, is_admin=True)
    db.add(member)
    db.commit()
    return RedirectResponse(url=f"/chat/{group.id}", status_code=302)

@app.post("/api/groups/join")
def join_group(request: Request, name: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    group = db.query(models.Group).filter(models.Group.name == name).first()
    if not group or not verify_password(password, group.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid group name or password")
    existing = db.query(models.GroupMember).filter(
        models.GroupMember.user_id == user.id,
        models.GroupMember.group_id == group.id
    ).first()
    if existing:
        return RedirectResponse(url=f"/chat/{group.id}", status_code=302)
    member = models.GroupMember(user_id=user.id, group_id=group.id)
    db.add(member)
    db.commit()
    return RedirectResponse(url=f"/chat/{group.id}", status_code=302)

@app.get("/api/groups/join-invite/{invite_code}")
def join_via_invite(invite_code: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        # Store invite code in cookie, redirect to register page
        response = RedirectResponse(url=f"/register?invite={invite_code}", status_code=302)
        response.set_cookie("pending_invite", invite_code, max_age=600)
        return response
    group = db.query(models.Group).filter(models.Group.invite_code == invite_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Invalid invite link")
    existing = db.query(models.GroupMember).filter(
        models.GroupMember.user_id == user.id,
        models.GroupMember.group_id == group.id
    ).first()
    if not existing:
        member = models.GroupMember(user_id=user.id, group_id=group.id)
        db.add(member)
        db.commit()
    return RedirectResponse(url=f"/chat/{group.id}", status_code=302)

@app.post("/api/messages/send")
async def send_message(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    body = await request.json()
    group_id = body.get("group_id")
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Empty message")
    member = db.query(models.GroupMember).filter(
        models.GroupMember.user_id == user.id,
        models.GroupMember.group_id == group_id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    msg = models.Message(content=content, user_id=user.id, group_id=group_id)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {
        "id": msg.id,
        "content": msg.content,
        "sender": user.username,
        "created_at": msg.created_at.strftime("%H:%M")
    }

@app.get("/api/messages/{group_id}")
def get_messages(group_id: int, request: Request, since_id: int = 0, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    msgs = db.query(models.Message).filter(
        models.Message.group_id == group_id,
        models.Message.id > since_id
    ).order_by(models.Message.created_at).all()
    return [
        {
            "id": m.id,
            "content": m.content,
            "sender": m.sender.username,
            "created_at": m.created_at.strftime("%H:%M"),
            "is_me": m.user_id == user.id
        }
        for m in msgs
    ]

@app.post("/api/recommend/{group_id}")
def recommend(group_id: int, request: Request, db: Session = Depends(get_db)):
    from nlp import analyze_chat
    from recommender import rank_destinations

    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    member = db.query(models.GroupMember).filter(
        models.GroupMember.user_id == user.id,
        models.GroupMember.group_id == group_id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")

    messages = db.query(models.Message).filter(
        models.Message.group_id == group_id
    ).order_by(models.Message.created_at).all()

    if len(messages) < 1:
        raise HTTPException(status_code=400, detail="No messages to analyze")

    chat_data = [{"sender": m.sender.username, "content": m.content} for m in messages]
    analysis = analyze_chat(chat_data)
    recommendations = rank_destinations(analysis)

    return {
        "analysis": {
            "budget":           analysis["budget"],
            "top_vibes":        analysis["top_vibes"],
            "starting_city":    analysis["starting_city"],
            "total_users":      analysis["total_users"],
            "preferred_states": analysis.get("preferred_states", []),
            "excluded_vibes":   analysis.get("excluded_vibes", []),
        },
        "recommendations": recommendations.get("city_clusters", [])
    }

@app.post("/api/feedback/{group_id}")
async def submit_feedback(group_id: int, request: Request, db: Session = Depends(get_db)):
    import csv, os
    from datetime import datetime

    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    body = await request.json()

    feedback_row = {
        "timestamp":              datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "group_id":               group_id,
        "username":               user.username,
        "recommended_city":       body.get("recommended_city", ""),
        "destination_relevance":  body.get("destination_relevance", ""),
        "budget_accuracy":        body.get("budget_accuracy", ""),
        "vibe_match":             body.get("vibe_match", ""),
        "overall_satisfaction":   body.get("overall_satisfaction", ""),
        "would_use_again":        body.get("would_use_again", ""),
        "comments":               body.get("comments", "").strip(),
    }

    feedback_path = os.path.join(os.path.dirname(__file__), "data", "feedback.csv")
    file_exists   = os.path.exists(feedback_path)

    with open(feedback_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=feedback_row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(feedback_row)

    return {"status": "saved", "message": "Thank you for your feedback!"}
