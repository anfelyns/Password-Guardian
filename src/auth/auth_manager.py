# -*- coding: utf-8 -*-
# auth_manager.py - Updated with proper password hashing

import os
import random
import string
import smtplib
import hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database.engine import SessionLocal
from database.models import User, OTPCode
from sqlalchemy import select, update


# ----------------- Password Hashing -----------------
def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """
    Hash password using PBKDF2-HMAC-SHA256
    Returns: (password_hash, salt)
    """
    if salt is None:
        salt = os.urandom(32).hex()
    
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # 100,000 iterations
    )
    
    return pwd_hash.hex(), salt


def verify_password(stored_hash: str, salt: str, provided_password: str) -> bool:
    """
    Verify a password against its hash
    Returns: True if password matches
    """
    pwd_hash, _ = hash_password(provided_password, salt)
    return pwd_hash == stored_hash


# ----------------- Auth Manager Class -----------------
class AuthManager:
    def __init__(self):
        self.email_cfg = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "youremail@gmail.com",
            "sender_password": "jouckunpvjzxnskx",
            "sender_name": "SecureVault",
        }
        # in-memory caches
        self.pending_2fa: dict[object, dict] = {}
        self.pending_reset: dict[str, dict] = {}
        self.pending_verify: dict[str, dict] = {}
        self._last_password = None

    # ---- normalize email key ----
    def _key(self, email_or_key) -> object:
        if isinstance(email_or_key, str):
            return email_or_key.strip().lower()
        return email_or_key

    def _send_mail(self, to_email: str, subject: str, body: str, html: bool = False) -> bool:
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_cfg['sender_name']} <{self.email_cfg['sender_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html' if html else 'plain'))
            
            s = smtplib.SMTP(self.email_cfg["smtp_server"], self.email_cfg["smtp_port"])
            s.starttls()
            s.login(self.email_cfg["sender_email"], self.email_cfg["sender_password"])
            s.send_message(msg)
            s.quit()
            
            print(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False

    def _gen_code(self, n=6) -> str:
        return ''.join(random.choice(string.digits) for _ in range(n))

    # ------------ DB ops ------------
    def _user_by_email(self, email: str) -> dict | None:
        k = self._key(email)
        with SessionLocal() as s:
            row = s.execute(select(User).where(User.email == k)).first()
            if not row:
                return None
            u: User = row[0]
            return {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "password_hash": u.password_hash,
                "salt": u.salt,
                "email_verified": u.email_verified,
            }

    def _set_password(self, email: str, new_password: str) -> bool:
        pw_hash, salt = hash_password(new_password)
        k = self._key(email)
        
        with SessionLocal() as s:
            s.execute(
                update(User)
                .where(User.email == k)
                .values(password_hash=pw_hash, salt=salt)
            )
            s.commit()
            return True

    def _create_user(self, username: str, email: str, password: str) -> int | None:
        pw_hash, salt = hash_password(password)
        k = self._key(email)
        
        with SessionLocal() as s:
            u = User(
                username=username,
                email=k,
                password_hash=pw_hash,
                salt=salt,
                email_verified=False,
                created_at=datetime.utcnow(),
            )
            s.add(u)
            s.commit()
            s.refresh(u)
            print(f"✅ User created: {username} (ID: {u.id})")
            return u.id

    # ------------ Public API ------------
    def register_user(self, username: str, email: str, password: str):
        existing = self._user_by_email(email)
        if existing:
            return False, "❌ Cet e-mail est déjà utilisé.", {}
        
        try:
            user_id = self._create_user(username, email, password)
            if not user_id:
                return False, "❌ Impossible de créer le compte.", {}

            code = self._gen_code()
            k = self._key(email)
            self.pending_verify[k] = {
                "code": str(code),
                "expires": datetime.utcnow() + timedelta(minutes=15),
                "user_id": user_id,
            }
            
            self._send_mail(
                email,
                "Vérification de votre compte – SecureVault",
                f"Bonjour {username},\n\nVotre code: {code}\n\nExpire dans 15 min.\n\nSecureVault"
            )
            
            print(f"[DEV] Registration code for {k}: {code}")
            return True, "✅ Code de vérification envoyé à votre e-mail.", {"user_id": user_id, "email": k}
            
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False, f"❌ Erreur lors de la création du compte: {e}", {}

    def verify_registration_code(self, email: str, code: str) -> bool:
        k = self._key(email)
        entry = self.pending_verify.get(k)
        
        if not entry:
            print(f"❌ No pending verification for {k}")
            return False
        
        if datetime.utcnow() > entry["expires"]:
            print(f"❌ Verification code expired for {k}")
            self.pending_verify.pop(k, None)
            return False
        
        if str(entry["code"]) != str(code).strip():
            print(f"❌ Invalid registration code for {k}")
            return False
        
        with SessionLocal() as s:
            s.execute(update(User).where(User.email == k).values(email_verified=True))
            s.commit()
        
        print(f"✅ User verified: {k}")
        self.pending_verify.pop(k, None)
        return True

    def authenticate(self, email: str, password: str) -> dict:
        """Authenticate user with password hashing verification"""
        try:
            u = self._user_by_email(email)
            
            if not u:
                return {
                    "error": "❌ Aucun compte trouvé avec cet email.\n\nVeuillez créer un compte.", 
                    "2fa_sent": False
                }
            
            # Check email verification
            if not u.get("email_verified"):
                return {
                    "error": (
                        "❌ Email non vérifié.\n\n"
                        "Veuillez vérifier votre boîte mail et entrer le code de vérification.\n\n"
                        "Si vous n'avez pas reçu le code, créez un nouveau compte."
                    ),
                    "2fa_sent": False,
                    "email_not_verified": True,
                    "user": {
                        "id": u['id'],
                        "username": u['username'],
                        "email": u['email']
                    }
                }
            
            # Verify password using hashing
            if not verify_password(u["password_hash"], u["salt"], password):
                return {
                    "error": "❌ Mot de passe incorrect.\n\nVeuillez réessayer.", 
                    "2fa_sent": False
                }

            self._last_password = password

            # Send 2FA code
            code = self._gen_code()
            k = self._key(email)
            self.pending_2fa[k] = {
                "code": str(code),
                "expires": datetime.utcnow() + timedelta(minutes=10),
                "user_id": u['id'],
                "purpose": "login",
            }
            
            print(f"[DEV] 2FA code for {k}: {code}")

            self._send_mail(
                email,
                "Votre code 2FA – SecureVault",
                f"Bonjour {u['username']},\n\n"
                f"Votre code de connexion: {code}\n\n"
                f"Ce code expire dans 10 minutes.\n\n"
                f"SecureVault"
            )
            
            return {
                "error": None,
                "2fa_sent": True,
                "user": {
                    "id": u['id'],
                    "username": u['username'],
                    "email": u['email'],
                    "salt": u['salt'],
                }
            }
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"❌ Erreur: {e}", "2fa_sent": False}

    def verify_2fa_email(self, email: str, code: str) -> bool:
        k = self._key(email)
        entry = self.pending_2fa.get(k)
        
        if not entry:
            print(f"❌ No pending 2FA for {k}")
            return False
        
        if datetime.utcnow() > entry["expires"]:
            print(f"❌ 2FA code expired for {k}")
            self.pending_2fa.pop(k, None)
            return False
        
        ok = (str(entry["code"]) == str(code).strip())
        if ok:
            print(f"✅ 2FA verified for {k}")
            self.pending_2fa.pop(k, None)
        else:
            print(f"❌ Invalid 2FA code for {k}")
        
        return ok

    def send_2fa_code(self, to_email: str, user_id: int | None = None, purpose: str = "sensitive_action") -> bool:
        u = self._user_by_email(to_email)
        if not u:
            print(f"❌ User not found: {to_email}")
            return False
        
        code = self._gen_code()
        expiry = datetime.utcnow() + timedelta(minutes=5)
        k = self._key(to_email)
        
        self.pending_2fa[k] = {
            "code": str(code), 
            "expires": expiry, 
            "purpose": purpose, 
            "user_id": u['id']
        }
        
        if user_id is not None:
            self.pending_2fa[user_id] = {
                "code": str(code), 
                "expires": expiry, 
                "purpose": purpose
            }
        
        print(f"[DEV] 2FA code for {k} ({purpose}): {code}")
        
        html = f"""
        <html><body>
        <h2>🔐 Vérification de sécurité</h2>
        <p>Code: <b style="font-size:24px;letter-spacing:6px;">{code}</b></p>
        <p>Ce code expire dans 5 minutes.</p>
        </body></html>
        """
        return self._send_mail(to_email, "🔐 Code de vérification - SecureVault", html, html=True)

    def verify_2fa(self, user_id_or_email, code: str) -> bool:
        key = self._key(user_id_or_email) if isinstance(user_id_or_email, str) else user_id_or_email
        entry = self.pending_2fa.get(key)
        
        if not entry:
            print(f"❌ No 2FA code found for: {key}")
            return False
        
        if datetime.utcnow() > entry["expires"]:
            print(f"⏰ 2FA code expired for: {key}")
            self.pending_2fa.pop(key, None)
            return False
        
        if str(entry["code"]) == str(code).strip():
            print(f"✅ 2FA code verified for: {key}")
            self.pending_2fa.pop(key, None)
            return True
        
        print(f"❌ Invalid 2FA code for: {key}")
        return False

    def send_reset_code(self, email: str) -> bool:
        u = self._user_by_email(email)
        if not u:
            print(f"❌ User not found for reset: {email}")
            return False
        
        code = self._gen_code()
        k = self._key(email)
        self.pending_reset[k] = {
            "code": str(code), 
            "expires": datetime.utcnow() + timedelta(minutes=15)
        }
        
        ok = self._send_mail(
            email,
            "Réinitialisation du mot de passe – SecureVault",
            f"Bonjour {u['username']},\n\nVotre code: {code}\n\nExpire dans 15 min.\n\nSecureVault"
        )
        
        if ok:
            print(f"[DEV] Reset code for {k}: {code}")
        
        return ok

    def verify_reset_code(self, email: str, code: str) -> bool:
        k = self._key(email)
        entry = self.pending_reset.get(k)
        
        if not entry:
            return False
        
        return (str(entry["code"]) == str(code).strip() 
                and datetime.utcnow() < entry["expires"])

    def update_password_with_code(self, email: str, code: str, new_password: str) -> bool:
        if not self.verify_reset_code(email, code):
            print(f"❌ Invalid reset code for {email}")
            return False
        
        ok = self._set_password(email, new_password)
        if ok:
            self.pending_reset.pop(self._key(email), None)
            print(f"✅ Password updated for {email}")
        
        return ok
    
    def resend_verification_code(self, email: str) -> bool:
        """Resend email verification code"""
        k = self._key(email)
        
        u = self._user_by_email(email)
        if not u:
            print(f"❌ User not found: {email}")
            return False
        
        if u.get('email_verified'):
            print(f"ℹ️ Email already verified: {email}")
            return False
        
        code = self._gen_code()
        self.pending_verify[k] = {
            "code": str(code),
            "expires": datetime.utcnow() + timedelta(minutes=15),
            "user_id": u['id'],
        }
        
        self._send_mail(
            email,
            "Vérification de votre compte – SecureVault",
            f"Bonjour {u['username']},\n\n"
            f"Votre nouveau code de vérification: {code}\n\n"
            f"Ce code expire dans 15 minutes.\n\n"
            f"SecureVault"
        )
        
        print(f"[DEV] New verification code for {k}: {code}")
        return True
