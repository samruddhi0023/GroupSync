from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String, unique=True, index=True, nullable=False)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    group_memberships = relationship("GroupMember", back_populates="user")
    messages          = relationship("Message",     back_populates="sender")


class Group(Base):
    __tablename__ = "groups"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    invite_code     = Column(String, unique=True, index=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    created_by      = Column(Integer, ForeignKey("users.id"))

    members  = relationship("GroupMember", back_populates="group")
    messages = relationship("Message",     back_populates="group")


class GroupMember(Base):
    __tablename__ = "group_members"

    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"),  nullable=False)
    group_id  = Column(Integer, ForeignKey("groups.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_admin  = Column(Boolean, default=False)

    user  = relationship("User",  back_populates="group_memberships")
    group = relationship("Group", back_populates="members")


class Message(Base):
    __tablename__ = "messages"

    id         = Column(Integer, primary_key=True, index=True)
    content    = Column(Text, nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id"),  nullable=False)
    group_id   = Column(Integer, ForeignKey("groups.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User",  back_populates="messages")
    group  = relationship("Group", back_populates="messages")