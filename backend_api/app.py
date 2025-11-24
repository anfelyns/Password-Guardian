# backend_api/app.py - FIXED DATABASE CONNECTION
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, TIMESTAMP, func, ForeignKey, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import re

app = Flask(__name__)
CORS(app)


DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "inessouai2005_")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "password_guardian")

print("=" * 60)
print("🔧 Database Configuration:")
print(f"   User: {DB_USER}")
print(f"   Host: {DB_HOST}:{DB_PORT}")
print(f"   Database: {DB_NAME}")
print(f"   Password: {'***' if DB_PASS else '(empty)'}")
print("=" * 60)

try:
    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        pool_pre_ping=True,
        echo=False
    )
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Database connection successful!")
except Exception as e:
    print(f"❌ Database connection FAILED: {e}")
    print("\n💡 Fix this by:")
    print("   1. Check your MySQL is running")
    print("   2. Update DB_PASS in app.py (line 17)")
    print("   3. Or set environment variable: DB_PASS=your_password")
    import sys
    sys.exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------- Models ----------
class Password(Base):
    __tablename__ = "passwords"
    __table_args__ = {'extend_existing': True}  # ✅ Don't recreate existing table

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # ✅ Removed ForeignKey to avoid conflicts
    site_name = Column(String(100), nullable=False)
    site_url = Column(String(500), nullable=True)
    site_icon = Column(String(10), default="🔒")
    username = Column(String(255), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    category = Column(String(30), default="personal", index=True)
    strength = Column(String(20), default="medium", index=True)
    favorite = Column(Boolean, default=False, index=True)
    trashed_at = Column(TIMESTAMP, nullable=True)
    last_updated = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# ---------- Helper Functions ----------
def calculate_password_strength(password: str) -> str:
    """Calculate password strength. Returns: weak, medium, strong"""
    if not password:
        return "weak"

    score = 0
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"[a-z]", password):
        score += 1
    if re.search(r"[0-9]", password):
        score += 1
    if re.search(r"[!@#$%^&*()\-_=+\[\]{};:,.<>/?]", password):
        score += 1

    if score <= 2:
        return "weak"
    elif score <= 4:
        return "medium"
    else:
        return "strong"


# ---------- Routes ----------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "timestamp": datetime.utcnow().isoformat()})


@app.route('/passwords', methods=['POST'])
def add_password():
    try:
        data = request.get_json()
        print(f"📥 Adding password: {data.get('site_name')}")
        
        user_id = data.get('user_id')
        site_name = data.get('site_name')
        username = data.get('username')
        encrypted_password = data.get('encrypted_password')
        category = data.get('category', 'personal')
        site_url = data.get('site_url', '')
        
        if not all([user_id, site_name, username, encrypted_password]):
            return jsonify({"error": "Missing required fields"}), 400
        
        strength = calculate_password_strength(encrypted_password)
        
        new_password = Password(
            user_id=user_id,
            site_name=site_name,
            site_url=site_url,
            username=username,
            encrypted_password=encrypted_password,
            category=category,
            strength=strength,
            favorite=False,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        with SessionLocal() as session:
            session.add(new_password)
            session.commit()
            session.refresh(new_password)
            
            print(f"✅ Password added: ID={new_password.id}")
            
            return jsonify({
                "id": new_password.id,
                "site_name": new_password.site_name,
                "site_url": new_password.site_url,
                "username": new_password.username,
                "category": new_password.category,
                "strength": new_password.strength,
                "created_at": new_password.created_at.isoformat()
            }), 201
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/passwords/<int:user_id>', methods=['GET'])
def get_passwords(user_id):
    try:
        with SessionLocal() as session:
            passwords = session.query(Password).filter(Password.user_id == user_id).all()
            
            result = []
            for pwd in passwords:
                result.append({
                    "id": pwd.id,
                    "site_name": pwd.site_name,
                    "site_url": getattr(pwd, 'site_url', ''),
                    "site_icon": pwd.site_icon or "🔒",
                    "username": pwd.username,
                    "encrypted_password": pwd.encrypted_password,
                    "category": pwd.category,
                    "strength": pwd.strength,
                    "favorite": pwd.favorite,
                    "last_updated": pwd.last_updated.strftime("%d/%m/%Y") if pwd.last_updated else "",
                    "created_at": pwd.created_at.isoformat() if pwd.created_at else ""
                })
            
            print(f"✅ Returned {len(result)} passwords for user {user_id}")
            return jsonify(result), 200
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/passwords/<int:password_id>', methods=['PUT'])
def update_password(password_id):
    try:
        data = request.get_json()
        
        with SessionLocal() as session:
            pwd = session.query(Password).filter(Password.id == password_id).first()
            
            if not pwd:
                return jsonify({"error": "Password not found"}), 404
            
            if 'site_name' in data:
                pwd.site_name = data['site_name']
            if 'site_url' in data:
                pwd.site_url = data['site_url']
            if 'username' in data:
                pwd.username = data['username']
            if 'encrypted_password' in data:
                pwd.encrypted_password = data['encrypted_password']
                pwd.strength = calculate_password_strength(data['encrypted_password'])
            if 'category' in data:
                pwd.category = data['category']
            if 'favorite' in data:
                pwd.favorite = data['favorite']
            
            pwd.last_updated = datetime.utcnow()
            session.commit()
            
            return jsonify({"message": "Password updated successfully"}), 200
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/passwords/<int:password_id>', methods=['DELETE'])
def delete_password(password_id):
    try:
        with SessionLocal() as session:
            pwd = session.query(Password).filter(Password.id == password_id).first()
            
            if not pwd:
                return jsonify({"error": "Password not found"}), 404
            
            session.delete(pwd)
            session.commit()
            
            return jsonify({"message": "Password deleted"}), 200
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/passwords/<int:password_id>/reveal', methods=['GET'])
def reveal_password(password_id):
    try:
        with SessionLocal() as session:
            pwd = session.query(Password).filter(Password.id == password_id).first()
            
            if not pwd:
                return jsonify({"error": "Password not found"}), 404
            
            return jsonify({"encrypted_password": pwd.encrypted_password}), 200
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/passwords/<int:pwd_id>/favorite", methods=["PATCH"])
def toggle_favorite(pwd_id: int):
    try:
        with SessionLocal() as session:
            pwd = session.query(Password).filter(Password.id == pwd_id).first()
            
            if not pwd:
                return jsonify({"error": "Password not found"}), 404
            
            pwd.favorite = not bool(pwd.favorite)
            session.commit()
            
            return jsonify({"ok": True, "favorite": bool(pwd.favorite)}), 200
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


# ---------- Run App ----------
if __name__ == "__main__":
    print("\n🚀 Starting Flask server on http://127.0.0.1:5001")
    print("   Press Ctrl+C to stop\n")
    app.run(host="127.0.0.1", port=5001, debug=True)