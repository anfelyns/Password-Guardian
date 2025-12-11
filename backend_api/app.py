# -*- coding: utf-8 -*-
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, TIMESTAMP, func, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import re
import base64
import hashlib
from cryptography.fernet import Fernet

# -------------------------------------------------------------------
# Flask init
# -------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# -------------------------------------------------------------------
# Database configuration
# -------------------------------------------------------------------
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "hatiyourpassword")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "password_guardian")

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------------------------------------------------
# Encryption system
# -------------------------------------------------------------------
MASTER_PASSWORD = "YourSecretMasterPassword2024!"

def get_fernet_key():
    """Generate Fernet-compatible AES-256 key"""
    kdf = hashlib.pbkdf2_hmac(
        'sha256',
        MASTER_PASSWORD.encode('utf-8'),
        b'salt_password_guardian_2024',
        100000
    )
    return base64.urlsafe_b64encode(kdf[:32])

cipher = Fernet(get_fernet_key())

def encrypt_password(plain: str) -> str:
    """Encrypt plaintext password"""
    return cipher.encrypt(plain.encode("utf-8")).decode("utf-8")

def decrypt_password(enc: str) -> str:
    """Decrypt ciphertext password"""
    return cipher.decrypt(enc.encode("utf-8")).decode("utf-8")

# -------------------------------------------------------------------
# Database model (Password table)
# MUST match actual MySQL schema
# -------------------------------------------------------------------
class Password(Base):
    __tablename__ = "passwords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    site_name = Column(String(100), nullable=False)
    site_url = Column(String(500), nullable=True)
    site_icon = Column(String(10), default="🔒")

    username = Column(String(255), nullable=False)

    # IMPORTANT: the REAL column name in MySQL
    encrypted_password = Column(Text, nullable=False)

    category = Column(String(30), default="personal")
    strength = Column(String(20), default="medium")
    favorite = Column(Boolean, default=False)

    trashed_at = Column(TIMESTAMP, nullable=True)
    last_updated = Column(TIMESTAMP, server_default=func.current_timestamp(),
                          onupdate=func.current_timestamp())
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------
def calculate_strength(pwd: str):
    score = 0
    if len(pwd) >= 8: score += 1
    if len(pwd) >= 12: score += 1
    if re.search(r"[A-Z]", pwd): score += 1
    if re.search(r"[a-z]", pwd): score += 1
    if re.search(r"[0-9]", pwd): score += 1
    if re.search(r"[!@#$%^&*()\-_=+\[\]{};:,.<>/?]", pwd): score += 1

    if score <= 2: return "weak"
    if score <= 4: return "medium"
    return "strong"

# -------------------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------------------
@app.route("/health")
def health():
    return jsonify({"ok": True, "time": datetime.utcnow().isoformat()})

# -------------------------------------------------------------------
# ADD PASSWORD
# -------------------------------------------------------------------
@app.route("/passwords", methods=["POST"])
def add_password():
    try:
        data = request.get_json()

        user_id = data.get("user_id")
        site_name = data.get("site_name")
        site_url = data.get("site_url", "")
        username = data.get("username")
        plain_password = data.get("password")
        category = data.get("category", "personal")

        if not all([user_id, site_name, username, plain_password]):
            return jsonify({"error": "Missing required fields"}), 400

        encrypted = encrypt_password(plain_password)
        strength = calculate_strength(plain_password)

        new_pwd = Password(
            user_id=user_id,
            site_name=site_name,
            site_url=site_url,
            username=username,
            encrypted_password=encrypted,  # FIXED
            category=category,
            strength=strength,
            favorite=False,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )

        with SessionLocal() as session:
            session.add(new_pwd)
            session.commit()
            session.refresh(new_pwd)

        return jsonify({
            "id": new_pwd.id,
            "site_name": new_pwd.site_name,
            "username": new_pwd.username,
            "category": new_pwd.category,
            "strength": new_pwd.strength,
            "created_at": new_pwd.created_at.isoformat(),
        }), 201

    except Exception as e:
        print("❌ Add password error:", e)
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------
# GET ALL PASSWORDS FOR USER
# -------------------------------------------------------------------
@app.route("/passwords/<int:user_id>", methods=["GET"])
def get_passwords(user_id):
    try:
        with SessionLocal() as session:
            pwds = session.query(Password).filter(
                Password.user_id == user_id,
                Password.trashed_at.is_(None)
            ).all()

        return jsonify([
            {
                "id": p.id,
                "site_name": p.site_name,
                "site_url": p.site_url,
                "site_icon": p.site_icon,
                "username": p.username,
                "category": p.category,
                "strength": p.strength,
                "favorite": p.favorite,
                "last_updated": p.last_updated.strftime("%d/%m/%Y"),
            }
            for p in pwds
        ])

    except Exception as e:
        print("❌ Get passwords error:", e)
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------
# REVEAL PASSWORD (Decrypt)
# -------------------------------------------------------------------
@app.route("/passwords/<int:password_id>/reveal", methods=["GET"])
def reveal(password_id):
    try:
        with SessionLocal() as session:
            pwd = session.query(Password).filter(Password.id == password_id).first()

        if not pwd:
            return jsonify({"error": "Not found"}), 404

        encrypted = pwd.encrypted_password
        if not encrypted:
            return jsonify({"error": "No encrypted password stored"}), 500

        plain = decrypt_password(encrypted)

        return jsonify({
            "password": plain,
            "username": pwd.username,
            "site_name": pwd.site_name,
            "site_url": pwd.site_url
        })

    except Exception as e:
        print("❌ Reveal decrypt failed:", e)
        return jsonify({"error": "Failed to decrypt password"}), 500

# -------------------------------------------------------------------
# UPDATE PASSWORD
# -------------------------------------------------------------------
@app.route("/passwords/<int:pid>", methods=["PUT"])
def update_password(pid):
    try:
        data = request.get_json()

        with SessionLocal() as session:
            pwd = session.query(Password).filter(Password.id == pid).first()
            if not pwd:
                return jsonify({"error": "Not found"}), 404

            if "site_name" in data:
                pwd.site_name = data["site_name"]

            if "site_url" in data:
                pwd.site_url = data["site_url"]

            if "username" in data:
                pwd.username = data["username"]

            if "password" in data:
                pwd.encrypted_password = encrypt_password(data["password"])
                pwd.strength = calculate_strength(data["password"])

            if "category" in data:
                pwd.category = data["category"]

            if "favorite" in data:
                pwd.favorite = bool(data["favorite"])

            pwd.last_updated = datetime.utcnow()
            session.commit()

        return jsonify({"message": "Updated"}), 200

    except Exception as e:
        print("❌ Update error:", e)
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------
# DELETE PASSWORD
# -------------------------------------------------------------------
@app.route("/passwords/<int:pid>", methods=["DELETE"])
def delete_password(pid):
    try:
        with SessionLocal() as session:
            pwd = session.query(Password).filter(Password.id == pid).first()
            if not pwd:
                return jsonify({"error": "Not found"}), 404

            session.delete(pwd)
            session.commit()

        return jsonify({"message": "Deleted"}), 200

    except Exception as e:
        print("❌ Delete error:", e)
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------
# TOGGLE FAVORITE STATUS
# -------------------------------------------------------------------
@app.route("/passwords/<int:pid>/favorite", methods=["PATCH", "PUT"])
def toggle_favorite(pid):
    try:
        print(f"\n🌟 Toggling favorite for password ID={pid}")
        
        with SessionLocal() as session:
            pwd = session.query(Password).filter(Password.id == pid).first()
            
            if not pwd:
                return jsonify({"error": "Password not found"}), 404
            
            pwd.favorite = not bool(pwd.favorite)
            pwd.last_updated = datetime.utcnow()
            session.commit()
            
            return jsonify({
                "ok": True, 
                "favorite": bool(pwd.favorite)
            }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------
# RUN BACKEND
# -------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
