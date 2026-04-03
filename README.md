# GroupSync — AI-Powered Group Trip Planner

A full-stack web app where your group chats and AI recommends the perfect destination.

---

## Quick Setup (5 minutes)

### 1. Prerequisites
- Python 3.9+
- pip

### 2. Install dependencies
```bash
pip install fastapi uvicorn sqlalchemy pandas python-jose[cryptography] passlib[bcrypt] jinja2 python-multipart numpy scikit-learn
```

### 3. Run the app
```bash
cd groupsync
uvicorn main:app --reload
```

### 4. Open in browser
```
http://127.0.0.1:8000
```

---

## How to Use

1. **Register** — Create an account at `/register`
2. **Create a Group** — From the Dashboard, create a group with a name + password
3. **Invite Friends** — Share the invite link (or group name + password)
4. **Chat** — Discuss travel preferences, budget, and trip vibes
5. **Get AI Recommendations** — Click **✦ Suggest Destinations** for personalized top 3 picks

### What to say in chat (examples)
- `"I want a beach vacation with water sports"`
- `"My budget is ₹3000 per day"`
- `"Starting from Mumbai, 5 days trip"`
- `"I love trekking and adventure"`
- `"Something cultural and historical"`

---

## Project Structure
```
groupsync/
├── main.py           # FastAPI app, routes, auth
├── database.py       # SQLAlchemy engine setup
├── models.py         # User, Group, GroupMember, Message
├── nlp.py            # NLP: extract budget, vibes, city from chat
├── recommender.py    # AI scoring & ranking algorithm
├── data/
│   └── destinations.csv   # 25 Indian travel destinations dataset
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── chat.html
├── static/
│   ├── style.css
│   └── script.js
└── requirements.txt
```

---

## AI Recommendation Algorithm

The AI analyzes all chat messages and computes a **Ranking Score** per destination:

```
R = α(Vibe Score) + β(Budget Score) + γ(Group Suitability) + δ(Rating) - λ(Penalty)

Where:
  α = 0.35  (vibe/interest matching)
  β = 0.25  (budget fit)
  γ = 0.20  (group suitability from dataset)
  δ = 0.20  (destination rating)
  λ = 0.30  (penalty if over budget)
```

**Group Satisfaction** measures how well a destination serves each individual member and the whole group equally (fairness index).

---

## Optional: Enable Gemini AI

For enhanced NLP, add your Gemini API key:
```bash
pip install google-generativeai
export GEMINI_API_KEY=your_key_here
```
Then modify `nlp.py` to use `google.generativeai` for deeper chat analysis.

---

## Tech Stack
- **Backend**: FastAPI + Python
- **Database**: SQLite via SQLAlchemy
- **Auth**: JWT (python-jose) + bcrypt passwords
- **NLP**: Custom Python keyword extraction
- **Frontend**: HTML + CSS + Vanilla JavaScript
- **Data**: Pandas + 25-destination CSV dataset
