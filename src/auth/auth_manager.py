# auth_manager.py
"""
AuthManager for SecureVault (ORM + email)
- Proper DB user verification (SQLAlchemy)
- Email verification codes
- 2FA authentication (email)
- Password reset codes
- 2FA for sensitive ops
- Normalized email keys for 2FA caches to avoid 'incorrect code' issues
"""
import os
import random
import string
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database.engine import SessionLocal
from database.models import User, OTPCode
from sqlalchemy import select, update

import hashlib

# ----------------- helpers -----------------
def _pbkdf2(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    if not salt_hex:
        salt_hex = os.urandom(32).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_hex.encode("utf-8"), 100000)
    return h.hex(), salt_hex

# ----------------- class -------------------
class AuthManager:
    def __init__(self):
        self.email_cfg = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "inessouai2005@gmail.com",
            "sender_password": "jouckunpvjzxnskx",
            "sender_name": "SecureVault",
        }
        # in-memory caches
        self.pending_2fa: dict[object, dict] = {}
        self.pending_reset: dict[str, dict] = {}
        self.pending_verify: dict[str, dict] = {}
        self._last_password = None  # optional master key usage downstream

    # ---- normalize email key for pending dicts ----
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
        pw_hash, salt = _pbkdf2(new_password)
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
        pw_hash, salt = _pbkdf2(password)
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

    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        h, _ = _pbkdf2(password, salt)
        return (h == stored_hash)

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
        try:
            u = self._user_by_email(email)
            if not u:
                return {"error": "❌ Utilisateur non trouvé. Créez un compte.", "2fa_sent": False}
            if not u.get("email_verified"):
                return {"error": "❌ Email non vérifié. Vérifiez votre boîte mail.", "2fa_sent": False}
            if not self._verify_password(password, u["password_hash"], u["salt"]):
                return {"error": "❌ Mot de passe incorrect.", "2fa_sent": False}

            self._last_password = password  # optional master key usage

            code = self._gen_code()
            k = self._key(email)
            self.pending_2fa[k] = {
                "code": str(code),
                "expires": datetime.utcnow() + timedelta(minutes=10),
                "user_id": u['id'],
                "purpose": "login",
            }
            print(f"[DEV] 2FA code for {k}: {code}")  # show in console for testing

            self._send_mail(
                email,
                "Votre code 2FA – SecureVault",
                f"Bonjour {u['username']},\n\nVotre code de connexion: {code}\n\n"
                f"Ce code expire dans 10 minutes.\n\nSecureVault"
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
            print(f"❌ Invalid 2FA code for {k} (expected {entry['code']}, got {code})")
        return ok

    # 2FA for sensitive ops
    def send_2fa_code(self, to_email: str, user_id: int | None = None, purpose: str = "sensitive_action") -> bool:
        u = self._user_by_email(to_email)
        if not u:
            print(f"❌ User not found: {to_email}")
            return False
        code = self._gen_code()
        expiry = datetime.utcnow() + timedelta(minutes=5)
        k = self._key(to_email)
        self.pending_2fa[k] = {"code": str(code), "expires": expiry, "purpose": purpose, "user_id": u['id']}
        if user_id is not None:
            self.pending_2fa[user_id] = {"code": str(code), "expires": expiry, "purpose": purpose}
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

    # Password reset
    def send_reset_code(self, email: str) -> bool:
        u = self._user_by_email(email)
        if not u:
            print(f"❌ User not found for reset: {email}")
            return False
        code = self._gen_code()
        k = self._key(email)
        self.pending_reset[k] = {"code": str(code), "expires": datetime.utcnow() + timedelta(minutes=15)}
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
        return (str(entry["code"]) == str(code).strip() and datetime.utcnow() < entry["expires"])

    def update_password_with_code(self, email: str, code: str, new_password: str) -> bool:
        if not self.verify_reset_code(email, code):
            print(f"❌ Invalid reset code for {email}")
            return False
        ok = self._set_password(email, new_password)
        if ok:
            self.pending_reset.pop(self._key(email), None)
            print(f"✅ Password updated for {email}")
        return ok
