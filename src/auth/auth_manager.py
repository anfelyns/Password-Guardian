"""
Fixed AuthManager for SecureVault
- Proper database user verification
- Email verification with codes
- 2FA authentication
- Password reset functionality
- 2FA for sensitive operations (view/copy passwords)
"""

import random, string, smtplib, mysql.connector, hashlib, os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class AuthManager:
    def __init__(self, host='localhost', user='root', password='inessouai2005_', database='password_guardian', port=3306):
        self.db = dict(host=host, user=user, password=password, database=database, port=port)
        self.email = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "inessouai2005@gmail.com",
            "sender_password": "jouckunpvjzxnskx",
            "sender_name": "SecureVault"
        }
        self.pending_2fa = {}
        self.pending_reset = {}
        self.pending_verify = {}

    def _conn(self):
        return mysql.connector.connect(**self.db)

    def _hash_password(self, password, salt=None):
        """Hash password using PBKDF2"""
        if salt is None:
            salt = os.urandom(32).hex()
        
        pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return pw_hash.hex(), salt

    def _verify_password(self, password, stored_hash, salt):
        """Verify password against stored hash"""
        pw_hash, _ = self._hash_password(password, salt)
        return pw_hash == stored_hash

    def _user_by_email(self, email):
        """Get user by email from database"""
        q = "SELECT id, username, email, password_hash, salt, email_verified FROM users WHERE email=%s LIMIT 1"
        try:
            with self._conn() as cn:
                with cn.cursor(dictionary=True) as cur:
                    cur.execute(q, (email,))
                    return cur.fetchone()
        except Exception as e:
            print(f"❌ DB error in _user_by_email: {e}")
            return None

    def _set_password(self, email, new_password):
        """Update user password"""
        pw_hash, salt = self._hash_password(new_password)
        q = "UPDATE users SET password_hash=%s, salt=%s WHERE email=%s"
        try:
            with self._conn() as cn:
                with cn.cursor() as cur:
                    cur.execute(q, (pw_hash, salt, email))
                cn.commit()
                return True
        except Exception as e:
            print(f"❌ DB error in _set_password: {e}")
            return False

    def _create_user(self, username, email, password):
        """Create new user in database"""
        pw_hash, salt = self._hash_password(password)
        q = """
            INSERT INTO users (username, email, password_hash, salt, email_verified, created_at)
            VALUES (%s,%s,%s,%s,%s, NOW())
        """
        try:
            with self._conn() as cn:
                with cn.cursor() as cur:
                    cur.execute(q, (username, email, pw_hash, salt, 0))
                cn.commit()
                user_id = cur.lastrowid
                print(f"✅ User created: {username} (ID: {user_id})")
                return user_id
        except mysql.connector.IntegrityError as e:
            if "Duplicate entry" in str(e):
                print(f"❌ User already exists: {email}")
                return None
            raise
        except Exception as e:
            print(f"❌ DB error in _create_user: {e}")
            raise

    def _send_mail(self, to_email, subject, body, html=False):
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email['sender_name']} <{self.email['sender_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            s = smtplib.SMTP(self.email['smtp_server'], self.email['smtp_port'])
            s.starttls()
            s.login(self.email['sender_email'], self.email['sender_password'])
            s.send_message(msg)
            s.quit()
            
            print(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False

    def _gen_code(self, n=6):
        """Generate random numeric code"""
        return ''.join(random.choice(string.digits) for _ in range(n))

    def register_user(self, username: str, email: str, password: str):
        """
        Register new user
        Returns: (success, message, extra_data)
        """
        # Check if user already exists
        existing = self._user_by_email(email)
        if existing:
            return False, "❌ Cet e-mail est déjà utilisé.", {}

        try:
            # Create user in database
            user_id = self._create_user(username, email, password)
            if not user_id:
                return False, "❌ Impossible de créer le compte.", {}
            
            # Generate verification code
            code = self._gen_code()
            self.pending_verify[email] = {
                "code": code,
                "expires": datetime.utcnow() + timedelta(minutes=15),
                "user_id": user_id
            }
            
            # Send verification email
            self._send_mail(
                email,
                "Vérification de votre compte – SecureVault",
                f"Bonjour {username},\n\n"
                f"Votre code de vérification: {code}\n\n"
                f"Ce code expire dans 15 minutes.\n\n"
                f"Cordialement,\nL'équipe SecureVault"
            )
            
            print(f"✅ Registration code sent to {email}: {code}")
            return True, "✅ Code de vérification envoyé à votre e-mail.", {"user_id": user_id, "email": email}
            
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False, f"❌ Erreur lors de la création du compte: {str(e)}", {}

    def verify_registration_code(self, email: str, code: str):
        """Verify registration code and activate user"""
        entry = self.pending_verify.get(email)
        if not entry:
            print(f"❌ No pending verification for {email}")
            return False
        
        if datetime.utcnow() > entry["expires"]:
            print(f"❌ Verification code expired for {email}")
            return False
        
        if entry["code"] != code:
            print(f"❌ Invalid code for {email}")
            return False
        
        # Mark user as verified in database
        try:
            with self._conn() as cn:
                with cn.cursor() as cur:
                    cur.execute(
                        "UPDATE users SET email_verified=1 WHERE email=%s",
                        (email,)
                    )
                cn.commit()
            
            print(f"✅ User verified: {email}")
            self.pending_verify.pop(email, None)
            return True
            
        except Exception as e:
            print(f"❌ DB error in verify_registration_code: {e}")
            return False

    def authenticate(self, email: str, password: str):
        """
        Authenticate user with email and password
        Returns: dict with user info and 2fa_sent status
        """
        try:
            # Get user from database
            user = self._user_by_email(email)
            if not user:
                print(f"❌ User not found: {email}")
                return {"error": "❌ Utilisateur non trouvé. Créez un compte d'abord.", "2fa_sent": False}
            
            # Check if email is verified
            if not user.get('email_verified'):
                print(f"❌ Email not verified: {email}")
                return {"error": "❌ Email non vérifié. Vérifiez votre boîte mail.", "2fa_sent": False}
            
            # Verify password
            if not self._verify_password(password, user['password_hash'], user['salt']):
                print(f"❌ Invalid password for {email}")
                return {"error": "❌ Mot de passe incorrect.", "2fa_sent": False}
            
            # Generate and send 2FA code
            code = self._gen_code()
            self.pending_2fa[email] = {
                "code": code,
                "expires": datetime.utcnow() + timedelta(minutes=10),
                "user_id": user['id']
            }
            
            # Send 2FA email
            self._send_mail(
                email,
                "Votre code 2FA – SecureVault",
                f"Bonjour {user['username']},\n\n"
                f"Votre code de connexion: {code}\n\n"
                f"Ce code expire dans 10 minutes.\n\n"
                f"Si vous n'avez pas demandé cette connexion, ignorez cet email.\n\n"
                f"Cordialement,\nL'équipe SecureVault"
            )
            
            print(f"✅ 2FA code sent to {email}: {code}")
            
            # Return user info
            return {
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email']
                },
                "2fa_sent": True
            }
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return {"error": f"❌ Erreur: {str(e)}", "2fa_sent": False}

    def verify_2fa_email(self, email: str, code: str) -> bool:
        """Verify 2FA code"""
        entry = self.pending_2fa.get(email)
        if not entry:
            print(f"❌ No pending 2FA for {email}")
            return False
        
        if datetime.utcnow() > entry["expires"]:
            print(f"❌ 2FA code expired for {email}")
            return False
        
        ok = (entry["code"] == code)
        if ok:
            print(f"✅ 2FA verified for {email}")
            self.pending_2fa.pop(email, None)
        else:
            print(f"❌ Invalid 2FA code for {email}")
        
        return ok

    # ==========================================
    # NEW: 2FA FOR SENSITIVE OPERATIONS
    # ==========================================
    
    def send_2fa_code(self, to_email, user_id=None, purpose="sensitive_action"):
        """
        Send 2FA code for sensitive operations (view/copy passwords)
        
        Args:
            to_email (str): User's email
            user_id (int, optional): User ID
            purpose (str): Purpose of the code (login, sensitive_action, etc.)
            
        Returns:
            bool: True if code sent successfully
        """
        try:
            # Get user info
            user = self._user_by_email(to_email)
            if not user:
                print(f"❌ User not found: {to_email}")
                return False
            
            # Generate code
            code = self._gen_code()
            expiry = datetime.utcnow() + timedelta(minutes=5)  # 5 minute expiry
            
            # Store code (both by email and user_id for flexibility)
            self.pending_2fa[to_email] = {
                "code": code,
                "expires": expiry,
                "purpose": purpose,
                "user_id": user['id']
            }
            
            if user_id:
                self.pending_2fa[user_id] = {
                    "code": code,
                    "expires": expiry,
                    "purpose": purpose
                }
            
            # Create HTML email
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                            border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 40px; text-align: center;">
                    
                    <h1 style="color: #60a5fa; margin-bottom: 20px; font-size: 28px;">
                        🔐 Vérification de sécurité
                    </h1>
                    
                    <p style="font-size: 16px; color: #94a3b8; margin-bottom: 30px;">
                        Bonjour <strong>{user['username']}</strong>,<br><br>
                        Vous avez demandé à accéder à des informations sensibles.
                    </p>
                    
                    <div style="background: rgba(59, 130, 246, 0.1); border: 2px solid #3b82f6; 
                                border-radius: 12px; padding: 30px; margin: 30px 0;">
                        <p style="font-size: 14px; color: #94a3b8; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px;">
                            Votre code de vérification
                        </p>
                        <h2 style="font-size: 48px; color: #60a5fa; letter-spacing: 12px; 
                                   font-family: 'Courier New', monospace; margin: 10px 0; font-weight: bold;">
                            {code}
                        </h2>
                    </div>
                    
                    <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; 
                                padding: 16px; border-radius: 8px; margin: 20px 0; text-align: left;">
                        <p style="font-size: 13px; color: #fca5a5; margin: 0;">
                            ⏱️ <strong>Ce code expire dans 5 minutes</strong>
                        </p>
                    </div>
                    
                    <p style="font-size: 12px; color: #64748b; margin-top: 30px; line-height: 1.6;">
                        Si vous n'avez pas demandé ce code, veuillez ignorer cet email.<br>
                        Ne partagez jamais ce code avec qui que ce soit.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 30px 0;">
                    
                    <p style="font-size: 11px; color: #475569; margin: 0;">
                        © 2025 SecureVault - Gestionnaire de mots de passe sécurisé
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            success = self._send_mail(
                to_email,
                "🔐 Code de vérification - SecureVault",
                html_body,
                html=True
            )
            
            if success:
                print(f"✅ 2FA code for {purpose} sent to {to_email}: {code}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending 2FA code: {e}")
            return False

    def verify_2fa(self, user_id_or_email, code):
        """
        Verify 2FA code (works with both user_id and email)
        
        Args:
            user_id_or_email: User ID (int) or email (str)
            code (str): 6-digit code
            
        Returns:
            bool: True if valid, False otherwise
        """
        entry = self.pending_2fa.get(user_id_or_email)
        
        if not entry:
            print(f"❌ No 2FA code found for: {user_id_or_email}")
            return False
        
        if datetime.utcnow() > entry["expires"]:
            print(f"⏰ 2FA code expired for: {user_id_or_email}")
            # Clean up expired code
            self.pending_2fa.pop(user_id_or_email, None)
            return False
        
        if entry["code"] == code:
            print(f"✅ 2FA code verified for: {user_id_or_email}")
            # Clean up used code
            self.pending_2fa.pop(user_id_or_email, None)
            return True
        
        print(f"❌ Invalid 2FA code for: {user_id_or_email}")
        return False

    # ==========================================
    # PASSWORD RESET FUNCTIONALITY
    # ==========================================

    def send_reset_code(self, email: str) -> bool:
        """Send password reset code"""
        user = self._user_by_email(email)
        if not user:
            print(f"❌ User not found for reset: {email}")
            return False
        
        code = self._gen_code()
        self.pending_reset[email] = {
            "code": code,
            "expires": datetime.utcnow() + timedelta(minutes=15)
        }
        
        ok = self._send_mail(
            email,
            "Réinitialisation du mot de passe – SecureVault",
            f"Bonjour {user['username']},\n\n"
            f"Votre code de réinitialisation: {code}\n\n"
            f"Ce code expire dans 15 minutes.\n\n"
            f"Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.\n\n"
            f"Cordialement,\nL'équipe SecureVault"
        )
        
        if ok:
            print(f"✅ Reset code sent to {email}: {code}")
        
        return ok

    def verify_reset_code(self, email: str, code: str) -> bool:
        """Verify password reset code"""
        entry = self.pending_reset.get(email)
        if not entry:
            return False
        
        return (entry["code"] == code and datetime.utcnow() < entry["expires"])

    def update_password_with_code(self, email: str, code: str, new_password: str) -> bool:
        """Update password after verifying reset code"""
        if not self.verify_reset_code(email, code):
            print(f"❌ Invalid reset code for {email}")
            return False
        
        ok = self._set_password(email, new_password)
        if ok:
            self.pending_reset.pop(email, None)
            print(f"✅ Password updated for {email}")
        
        return ok