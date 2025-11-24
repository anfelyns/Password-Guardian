# database/models.py
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Boolean, DateTime, Text, ForeignKey,
    TIMESTAMP, func
)
from sqlalchemy.orm import (
    declarative_base, relationship, Mapped, mapped_column
)

Base = declarative_base()


# ============================================================
# USER MODEL
# ============================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    salt: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relations
    passwords: Mapped[List["Password"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    otp_codes: Mapped[List["OTPCode"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    devices: Mapped[List["UserDevice"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    activity_logs: Mapped[List["ActivityLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


# ============================================================
# PASSWORD MODEL
# ============================================================
class Password(Base):
    __tablename__ = "passwords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    site_name: Mapped[str] = mapped_column(String(100))
    site_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    site_icon: Mapped[Optional[str]] = mapped_column(String(10), default="🔒")
    username: Mapped[str] = mapped_column(String(255))
    encrypted_password: Mapped[str] = mapped_column(Text)

    category: Mapped[str] = mapped_column(String(50), default="personal", index=True)
    strength: Mapped[str] = mapped_column(String(20), default="medium", index=True)

    favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    trashed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    last_updated: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    # Relations
    user: Mapped["User"] = relationship(back_populates="passwords")
    history: Mapped[List["PasswordHistory"]] = relationship(
        back_populates="password", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Password(id={self.id}, site='{self.site_name}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "site_name": self.site_name,
            "site_url": self.site_url,
            "site_icon": self.site_icon,
            "username": self.username,
            "encrypted_password": self.encrypted_password,
            "category": self.category,
            "strength": self.strength,
            "favorite": self.favorite,
            "trashed_at": self.trashed_at.isoformat() if self.trashed_at else None,
            "last_updated": (
                self.last_updated.strftime("%Y-%m-%d %H:%M:%S") if self.last_updated else None
            ),
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
            )
        }


# ============================================================
# PASSWORD HISTORY
# ============================================================
class PasswordHistory(Base):
    __tablename__ = "password_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    password_id: Mapped[int] = mapped_column(
        ForeignKey("passwords.id", ondelete="CASCADE"), index=True
    )
    old_encrypted_password: Mapped[str] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    password: Mapped["Password"] = relationship(back_populates="history")


# ============================================================
# OTP CODE
# ============================================================
class OTPCode(Base):
    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(6))
    purpose: Mapped[str] = mapped_column(String(50), default="login")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="otp_codes")


# ============================================================
# SESSION MODEL
# ============================================================
class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    session_token: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    device_info: Mapped[Optional[str]] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="sessions")


# ============================================================
# USER DEVICE
# ============================================================
class UserDevice(Base):
    __tablename__ = "user_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    device_name: Mapped[str] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    last_used: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="devices")


# ============================================================
# ACTIVITY LOG
# ============================================================
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="activity_logs")