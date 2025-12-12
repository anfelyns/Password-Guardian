# -*- coding: utf-8 -*-
# auth_manager.py - Updated with proper password hashing

import os
import random
import string
import smtplib
import hashlib
import uuid
import html
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from database.engine import SessionLocal, engine
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
            "sender_email": "inessouai2005@gmail.com",
            "sender_password": "jouckunpvjzxnskx",
            "sender_name": "Password Guardian",
        }
        # in-memory caches
        self.pending_2fa: dict[object, dict] = {}
        self.pending_reset: dict[str, dict] = {}
        self.pending_verify: dict[str, dict] = {}
        self.failed_attempts: dict[str, dict] = {}
        self.active_sessions: dict[int, list] = {}
        self._last_password = None
    def _conn(self):
        return engine.raw_connection()

    # ---- normalize email key ----
    def _key(self, email_or_key) -> object:
        if isinstance(email_or_key, str):
            return email_or_key.strip().lower()
        return email_or_key

    def _send_mail(self, to_email: str, subject: str, plain_body: str, html_body: str | None = None) -> bool:
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_cfg['sender_name']} <{self.email_cfg['sender_email']}>"
            msg['To'] = to_email
            msg['Subject'] = str(Header(subject, 'utf-8'))
            plain_body = plain_body or "Password Guardian"
            msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            s = smtplib.SMTP(self.email_cfg["smtp_server"], self.email_cfg["smtp_port"])
            s.starttls()
            s.login(self.email_cfg["sender_email"], self.email_cfg["sender_password"])
            s.send_message(msg)
            s.quit()

            print(f"? Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"? Email error: {e}")
            return False


    def _gen_code(self, length: int = 6) -> str:
        return ''.join(random.choice(string.digits) for _ in range(length))

    def _build_email_template(
        self,
        title: str,
        greeting: str,
        highlight_value: str | None = None,
        highlight_label: str = "Code",
        details: list[str] | None = None,
        footer_note: str | None = None,
        cta: dict | None = None,
    ) -> tuple[str, str]:
        details = details or []
        footer_note = footer_note or "L'?quipe Password Guardian"
        esc = html.escape
        highlight_text = ""
        if highlight_value:
            highlight_text = f"{highlight_label}: {highlight_value}"
            highlight_html = f"""
                <div style='margin:18px 0;padding:18px;border-radius:18px;background:rgba(59,130,246,0.15);border:1px dashed rgba(255,255,255,0.35);text-align:center;'>
                    <div style='color:#93c5fd;font-size:12px;text-transform:uppercase;letter-spacing:1px;'>{esc(highlight_label)}</div>
                    <div style="font-size:30px;font-weight:700;color:#fff;letter-spacing:8px;font-family:'Roboto Mono','Segoe UI',monospace;user-select:all;margin-top:8px;">{esc(highlight_value)}</div>
                    <div style='margin-top:6px;font-size:12px;color:#94a3b8;'>Utilisez Ctrl+C ou appui long pour copier</div>
                </div>
            """
        else:
            highlight_html = ""
        detail_html = ""
        if details:
            rows = ''.join(f"<li style='margin-bottom:6px;'>{esc(item)}</li>" for item in details)
            detail_html = f"<ul style='padding-left:18px;color:#cbd5f5;font-size:13px;line-height:1.5;'>{rows}</ul>"
        cta_html = ""
        cta_text = ""
        if cta and cta.get('label') and cta.get('url'):
            label = esc(cta['label'])
            url = esc(cta['url'])
            cta_html = (
                f"<a href='{url}' style='display:inline-block;margin-top:18px;padding:12px 22px;"
                "background:#2563eb;border-radius:14px;color:#fff;font-weight:bold;text-decoration:none;'>"
                f"{label}</a>"
            )
            cta_text = f"Action: {cta['label']} -> {cta['url']}"
        body_html = f"""
        <html><body style="background:#020617;padding:32px;font-family:'Segoe UI','Roboto',sans-serif;">
            <table align='center' width='100%' style='max-width:520px;margin:0 auto;'>
                <tr>
                    <td style='background:#0f172a;border-radius:30px;padding:28px;border:1px solid rgba(255,255,255,0.08);color:#e2e8f0;'>
                        <div style='text-align:center;margin-bottom:12px;'>
                            <div style='font-size:42px;'>??</div>
                            <h2 style='margin:6px 0 0;font-size:24px;color:#fff;'>{esc(title)}</h2>
                        </div>
                        <p style='color:#cbd5f5;font-size:14px;line-height:1.6;'>{esc(greeting)}</p>
                        {highlight_html}
                        {detail_html}
                        {cta_html}
                        <p style='margin-top:26px;font-size:12px;color:#94a3b8;'>{esc(footer_note)}</p>
                    </td>
                </tr>
            </table>
        </body></html>
        """
        plain_lines = [title, "", greeting, ""]
        if highlight_text:
            plain_lines.append(highlight_text)
            plain_lines.append("")
        for item in details:
            plain_lines.append(f"- {item}")
        if cta_text:
            plain_lines.extend(["", cta_text])
        plain_lines.extend(["", footer_note])
        plain_body = "\n".join(line for line in plain_lines if line).strip() + "\n"
        return plain_body, body_html

    def _record_failed_attempt(self, email: str, username: str):
        """Increment failed login attempts and notify after threshold."""
        key = self._key(email)
        slot = self.failed_attempts.get(key, {"count": 0})
        slot["count"] = slot.get("count", 0) + 1
        slot["last"] = datetime.utcnow()
        self.failed_attempts[key] = slot

        if slot["count"] >= 5:
            self._notify_bruteforce_alert(email, username, slot["count"])
            slot["count"] = 0
            self.failed_attempts[key] = slot

    def _reset_failed_attempts(self, email: str):
        key = self._key(email)
        if key in self.failed_attempts:
            self.failed_attempts[key]["count"] = 0
            self.failed_attempts[key]["last"] = None

    def get_failed_attempts(self, email: str) -> int:
        key = self._key(email)
        entry = self.failed_attempts.get(key)
        if not entry:
            return 0
        return entry.get("count", 0)

    def _notify_bruteforce_alert(self, email: str, username: str, attempts: int):
        """Send an email alert when multiple failed attempts occur."""
        subject = "Alertes Password Guardian - Tentatives suspectes"
        greeting = (
            f"Bonjour {username}, nous avons bloqué {attempts} tentatives successives sur votre coffre."
        )
        plain, html_body = self._build_email_template(
            subject,
            greeting,
            highlight_value=str(attempts),
            highlight_label="Tentatives bloquées",
            details=[
                "Origine probable : saisie de mot de passe erronée ou personne malveillante.",
                "Nous vous recommandons de modifier votre mot de passe maître.",
                "Activez l'alerte « Appareil ajouté » dans les paramètres pour être averti à chaque connexion."
            ],
            footer_note="Besoin d'aide ? Répondez simplement à cet e-mail ou contactez le support Password Guardian."
        )
        self._send_mail(email, subject, plain, html_body)
        print(f"[SECURITY] Alert email sent to {email} after repeated failures")

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
            
            subject = "V?rification de votre compte ?? Password Guardian"
            plain, html_body = self._build_email_template(
                subject,
                f"Bonjour {username}, merci de rejoindre Password Guardian !",
                highlight_value=code,
                highlight_label="Code ? copier",
                details=[
                    "Saisissez ce code pour valider votre adresse e-mail.",
                    "Il expirera automatiquement dans 15 minutes.",
                    "Ne partagez jamais ce code avec une autre personne."
                ],
                footer_note="Password Guardian ? protection maximale de vos mots de passe."
            )
            self._send_mail(email, subject, plain, html_body)
            
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
                    "error": "❌ Aucun compte trouv? avec cet email.\n\nVeuillez cr?er un compte.",
                    "2fa_sent": False
                }

            if not u.get("email_verified"):
                return {
                    "error": (
                        "❌ Email non v?rifi?.\n\n"
                        "Veuillez v?rifier votre bo?te mail et entrer le code de v?rification.\n\n"
                        "Si vous n'avez pas re?u le code, cr?ez un nouveau compte."
                    ),
                    "2fa_sent": False,
                    "email_not_verified": True,
                    "user": {
                        "id": u['id'],
                        "username": u['username'],
                        "email": u['email']
                    }
                }

            if not verify_password(u["password_hash"], u["salt"], password):
                self._record_failed_attempt(email, u["username"])
                return {
                    "error": "❌ Mot de passe incorrect.\n\nVeuillez r?essayer.",
                    "2fa_sent": False
                }

            self._last_password = password
            self._reset_failed_attempts(email)

            code = self._gen_code()
            k = self._key(email)
            self.pending_2fa[k] = {
                "code": str(code),
                "expires": datetime.utcnow() + timedelta(minutes=10),
                "user_id": u['id'],
                "purpose": "login",
            }

            print(f"[DEV] 2FA code for {k}: {code}")

            subject = "🔒 Code de connexion ? Password Guardian"
            plain, html_body = self._build_email_template(
                subject,
                f"Bonjour {u['username']}, voici votre code de connexion s?curis?.",
                highlight_value=code,
                highlight_label="Code 2FA",
                details=[
                    "Valable 10 minutes pour finaliser votre connexion.",
                    f"Demande re?ue le {datetime.utcnow().strftime('%d/%m %H:%M')} (UTC).",
                    "Si ce n'?tait pas vous, changez imm?diatement votre mot de passe."
                ],
                footer_note="Password Guardian ? prot?gez tous vos secrets."
            )
            self._send_mail(email, subject, plain, html_body)

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

        subject = "🔒 Code de vérification - Password Guardian"
        purpose_text = {
            "login": "Connexion sécurisée",
            "device_revoke": "Suppression d'un appareil",
            "security_test": "Test de sécurité",
            "sensitive_action": "Action sensible",
            "revoke_all": "Révocation complète",
        }.get(purpose, "Validation en cours")
        expire_at = expiry.strftime('%d/%m %H:%M')
        plain, html_body = self._build_email_template(
            subject,
            f"Bonjour {u['username']}, voici votre code de validation.",
            highlight_value=code,
            highlight_label="Code 2FA",
            details=[
                f"Motif : {purpose_text}.",
                f"Expire le {expire_at} (UTC).",
                "Copiez le code puis collez-le dans Password Guardian pour confirmer l'opération."
            ],
            footer_note="Ne partagez jamais ce code, même avec une équipe Password Guardian."
        )
        return self._send_mail(to_email, subject, plain, html_body)

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
            print(f"? User not found for reset: {email}")
            return False
        
        code = self._gen_code()
        k = self._key(email)
        self.pending_reset[k] = {
            "code": str(code),
            "expires": datetime.utcnow() + timedelta(minutes=15)
        }
        
        subject = "R?initialisation du mot de passe ? Password Guardian"
        plain, html_body = self._build_email_template(
            subject,
            f"Bonjour {u['username']}, utilisez ce code pour r?initialiser votre mot de passe ma?tre.",
            highlight_value=code,
            highlight_label="Code de r?initialisation",
            details=[
                "Collez ce code dans l'application Password Guardian pour confirmer votre identit?.",
                "Le code reste valable pendant 15 minutes.",
                "Un nouvel e-mail annulera automatiquement ce code."
            ],
            footer_note="Password Guardian ne vous demandera jamais votre mot de passe complet par e-mail."
        )
        ok = self._send_mail(email, subject, plain, html_body)
        
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
            print(f"? User not found: {email}")
            return False
        
        if u.get('email_verified'):
            print(f"? Email already verified: {email}")
            return False
        
        code = self._gen_code()
        self.pending_verify[k] = {
            "code": str(code),
            "expires": datetime.utcnow() + timedelta(minutes=15),
            "user_id": u['id'],
        }
        
        subject = "Nouveau code de v?rification ? Password Guardian"
        plain, html_body = self._build_email_template(
            subject,
            f"Bonjour {u['username']}, voici un nouveau code pour v?rifier votre adresse e-mail.",
            highlight_value=code,
            highlight_label="Code ? copier",
            details=[
                "Il remplace tous les codes pr?c?dents et expirera dans 15 minutes.",
                "Collez-le dans Password Guardian pour finaliser votre inscription."
            ],
            footer_note="Merci de renforcer la s?curit? de votre coffre."
        )
        self._send_mail(email, subject, plain, html_body)
        print(f"[DEV] New verification code for {k}: {code}")
        return True

    # ----------------- Session tracking -----------------
    def register_session(self, user_id: int, device_name: str, system_info: str) -> str:
        session_id = uuid.uuid4().hex
        entry = {
            "session_id": session_id,
            "device": device_name,
            "system": system_info,
            "login_at": datetime.utcnow().isoformat(timespec="seconds")
        }
        sessions = self.active_sessions.setdefault(user_id, [])
        sessions.append(entry)
        # keep only last 10 sessions to limit growth
        if len(sessions) > 10:
            self.active_sessions[user_id] = sessions[-10:]
        return session_id

    def get_active_sessions(self, user_id: int) -> list:
        return list(self.active_sessions.get(user_id, []))

    def remove_session(self, user_id: int, session_id: str) -> bool:
        sessions = self.active_sessions.get(user_id, [])
        new_sessions = [s for s in sessions if s.get("session_id") != session_id]
        if len(new_sessions) == len(sessions):
            return False
        self.active_sessions[user_id] = new_sessions
        return True