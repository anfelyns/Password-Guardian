"""
Complete Authentication System for SecureVault
Includes user registration, login, email verification, and password management
"""
from passlib.hash import pbkdf2_sha256
import secrets
import string
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass


@dataclass
class User:
    """User data model"""
    id: int
    username: str
    email: str
    password_hash: str
    salt: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_verified: bool = False


class PasswordManager:
    """
    🔐 Password generation and strength evaluation
    """
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a strong secure password"""
        if length < 12:
            length = 12
        
        # Ensure at least one of each type
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*()-_=+[]{};:,.?/")
        ]
        
        # Fill the rest
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.?/"
        password += [secrets.choice(all_chars) for _ in range(length - 4)]
        
        # Shuffle
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    def evaluate_password_strength(password: str) -> Dict:
        """
        Evaluate password strength
        Returns: {level, score, suggestions, suggested_password}
        """
        suggestions = []
        score = 0
        
        # Length
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        else:
            suggestions.append("Utilisez au moins 8 caractères.")
        
        # Uppercase
        if re.search(r"[A-Z]", password):
            score += 1
        else:
            suggestions.append("Ajoutez une majuscule (A–Z).")
        
        # Lowercase
        if re.search(r"[a-z]", password):
            score += 1
        else:
            suggestions.append("Ajoutez une minuscule (a–z).")
        
        # Digits
        if re.search(r"\d", password):
            score += 1
        else:
            suggestions.append("Ajoutez un chiffre (0–9).")
        
        # Symbols
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            score += 1
        else:
            suggestions.append("Ajoutez un symbole (ex: !, @, #, $).")
        
        # Determine level
        if score >= 6:
            level = "strong"
        elif score >= 4:
            level = "medium"
        else:
            level = "weak"
        
        # Suggest strong password if needed
        suggested_password = None
        if level != "strong":
            suggested_password = PasswordManager.generate_secure_password()
        
        return {
            "level": level,
            "score": score,
            "suggestions": suggestions,
            "suggested_password": suggested_password
        }


class Authentication:
    """
    Complete authentication system with:
    - User registration with email verification
    - Secure password hashing (PBKDF2)
    - Login with device tracking
    - Email notifications
    """
    
    def __init__(self, db_connection, email_config: Dict):
        """
        Initialize authentication system
        
        Args:
            db_connection: Database connection function
            email_config: Email configuration dict with keys:
                - smtp_server
                - smtp_port
                - sender_email
                - sender_password
                - sender_name
        """
        self.get_db = db_connection
        self.email_config = email_config
    
    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        """
        Secure password hashing with PBKDF2
        Returns: (password_hash, salt)
        """
        salt = secrets.token_hex(16)
        password_hash = pbkdf2_sha256.hash(password + salt)
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash"""
        return pbkdf2_sha256.verify(password + salt, stored_hash)
    
    @staticmethod
    def _generate_verification_code(length: int = 6) -> str:
        """Generate numeric verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    def register_user(self, username: str, email: str, master_password: str) -> Tuple[bool, str, Dict]:
        """
        Register a new user with email verification
        
        Returns: (success, message, extra_data)
        """
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id, is_verified FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            
            # Evaluate password strength
            strength_eval = PasswordManager.evaluate_password_strength(master_password)
            
            if existing_user:
                user_id, is_verified = existing_user
                
                if is_verified:
                    cursor.close()
                    conn.close()
                    return False, "Un compte vérifié existe déjà avec cet email.", {}
                
                # User exists but not verified - update and resend code
                password_hash, salt = self.hash_password(master_password)
                verification_code = self._generate_verification_code()
                expires_at = datetime.now() + timedelta(minutes=10)
                
                cursor.execute("""
                    UPDATE users 
                    SET verification_code = %s, 
                        verification_expires_at = %s,
                        username = %s,
                        password_hash = %s,
                        salt = %s
                    WHERE email = %s AND is_verified = FALSE
                """, (verification_code, expires_at, username, password_hash, salt, email))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                # Send verification email
                self._send_verification_email(email, username, verification_code)
                
                extra_data = {
                    'user_id': user_id,
                    'two_factor_sent': True,
                    'password_strength': strength_eval
                }
                
                return True, "Un nouveau code de vérification a été envoyé.", extra_data
            
            # New user registration
            password_hash, salt = self.hash_password(master_password)
            verification_code = self._generate_verification_code()
            created_at = datetime.now()
            expires_at = datetime.now() + timedelta(minutes=10)
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, created_at, 
                                 is_verified, verification_code, verification_expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (username, email, password_hash, salt, created_at, False, verification_code, expires_at))
            
            user_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            
            # Send verification email
            self._send_verification_email(email, username, verification_code)
            
            extra_data = {
                'user_id': user_id,
                'two_factor_sent': True,
                'password_strength': strength_eval
            }
            
            return True, "Code de vérification envoyé à votre email.", extra_data
            
        except Exception as e:
            return False, f"Erreur lors de l'inscription: {str(e)}", {}
    
    def login_user(self, identifier: str, master_password: str, device_info: str = None) -> Tuple[bool, any, str]:
        """
        Login user with email/username
        
        Returns: (success, user_object, message)
        """
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, password_hash, salt, is_verified, last_device 
                FROM users WHERE username = %s OR email = %s
            """, (identifier, identifier))
            
            user_data = cursor.fetchone()
            
            if not user_data:
                cursor.close()
                conn.close()
                return False, None, "Utilisateur introuvable"
            
            user_id, username, email, stored_hash, salt, is_verified, last_device = user_data
            
            # Check if verified
            if not is_verified:
                cursor.close()
                conn.close()
                return False, None, "⚠️ Compte non vérifié. Vérifiez votre email."
            
            # Verify password
            if not self.verify_password(master_password, stored_hash, salt):
                cursor.close()
                conn.close()
                return False, None, "Mot de passe incorrect"
            
            # Check for new device
            if device_info and device_info != last_device:
                self._send_login_alert(email, username, device_info)
                cursor.execute("UPDATE users SET last_device = %s WHERE id = %s", (device_info, user_id))
                conn.commit()
            
            # Update last login
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # Create user object
            user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=stored_hash,
                salt=salt,
                is_verified=True
            )
            
            return True, user, "Connexion réussie"
            
        except Exception as e:
            return False, None, f"Erreur: {str(e)}"
    
    def verify_user_code(self, email: str, code: str) -> Tuple[bool, str]:
        """Verify email verification code"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, verification_code, verification_expires_at, is_verified 
                FROM users WHERE email = %s
            """, (email,))
            
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                conn.close()
                return False, "Aucun compte trouvé"
            
            user_id, username, stored_code, expires_at, is_verified = result
            
            if is_verified:
                cursor.close()
                conn.close()
                return False, "Compte déjà vérifié"
            
            # Check expiration
            if datetime.now() > expires_at:
                cursor.execute("""
                    UPDATE users 
                    SET verification_code = NULL, verification_expires_at = NULL
                    WHERE id = %s
                """, (user_id,))
                conn.commit()
                cursor.close()
                conn.close()
                return False, "⏰ Code expiré. Demandez un nouveau code."
            
            # Verify code
            if code != stored_code:
                time_remaining = int((expires_at - datetime.now()).total_seconds())
                cursor.close()
                conn.close()
                return False, f"Code incorrect. {time_remaining}s restantes."
            
            # Verify user
            cursor.execute("""
                UPDATE users 
                SET is_verified = TRUE, 
                    verification_code = NULL, 
                    verification_expires_at = NULL,
                    last_login = NOW()
                WHERE id = %s
            """, (user_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Send welcome email
            self._send_welcome_email(email, username)
            
            return True, "✅ Compte vérifié avec succès !"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def resend_verification_code(self, email: str) -> Tuple[bool, str]:
        """Resend verification code"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, is_verified 
                FROM users WHERE email = %s
            """, (email,))
            
            user_data = cursor.fetchone()
            
            if not user_data:
                cursor.close()
                conn.close()
                return False, "Aucun compte trouvé"
            
            user_id, username, is_verified = user_data
            
            if is_verified:
                cursor.close()
                conn.close()
                return False, "Compte déjà vérifié"
            
            # Generate new code
            new_code = self._generate_verification_code()
            new_expires = datetime.now() + timedelta(minutes=10)
            
            cursor.execute("""
                UPDATE users 
                SET verification_code = %s, verification_expires_at = %s
                WHERE email = %s
            """, (new_code, new_expires, email))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Send email
            self._send_verification_email(email, username, new_code)
            
            return True, "Nouveau code envoyé"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def _send_verification_email(self, email: str, username: str, code: str):
        """Send verification email with HTML template"""
        subject = "🔐 Code de vérification SecureVault"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0a1628; color: #e0e7ff; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a2942 0%, #0f1e36 100%); border-radius: 20px; padding: 40px; border: 1px solid rgba(96, 165, 250, 0.2);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #60a5fa; margin: 0;">🛡️ SecureVault</h1>
                    <p style="color: #94a3b8; margin-top: 10px;">Gestionnaire de mots de passe sécurisé</p>
                </div>
                
                <h2 style="color: #e0e7ff; margin-bottom: 20px;">Vérifiez votre compte</h2>
                
                <p style="color: #94a3b8; line-height: 1.6;">
                    Bonjour {username},<br><br>
                    Merci de vous être inscrit sur SecureVault ! 
                    Voici votre code de vérification :
                </p>
                
                <div style="background-color: rgba(16, 185, 129, 0.1); border: 2px solid #10b981; border-radius: 15px; padding: 30px; text-align: center; margin: 30px 0;">
                    <p style="color: #94a3b8; margin: 0 0 15px 0; font-size: 14px;">Code de vérification</p>
                    <p style="font-size: 42px; font-weight: bold; color: #10b981; letter-spacing: 8px; margin: 0; font-family: 'Courier New', monospace;">
                        {code}
                    </p>
                </div>
                
                <p style="color: #94a3b8; line-height: 1.6;">
                    Ce code est valide pendant <strong style="color: #e0e7ff;">10 minutes</strong>.
                </p>
                
                <p style="color: #64748b; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px;">
                    © 2025 SecureVault - Gestionnaire de mots de passe sécurisé
                </p>
            </div>
        </body>
        </html>
        """
        
        self._send_email(email, subject, html_body)
    
    def _send_welcome_email(self, email: str, username: str):
        """Send welcome email after verification"""
        subject = "🎉 Bienvenue sur SecureVault"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0a1628; color: #e0e7ff; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a2942 0%, #0f1e36 100%); border-radius: 20px; padding: 40px; border: 1px solid rgba(96, 165, 250, 0.2);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #60a5fa; margin: 0;">🛡️ SecureVault</h1>
                </div>
                
                <h2 style="color: #10b981;">🎉 Bienvenue {username} !</h2>
                
                <p style="color: #94a3b8; line-height: 1.6;">
                    Votre compte a été vérifié avec succès ! ✅<br><br>
                    Vous pouvez maintenant profiter de toutes les fonctionnalités de SecureVault :
                </p>
                
                <ul style="color: #94a3b8; line-height: 1.8;">
                    <li>Stockage sécurisé de vos mots de passe</li>
                    <li>Génération de mots de passe forts</li>
                    <li>Organisation par catégories</li>
                    <li>Chiffrement AES-256</li>
                </ul>
                
                <p style="color: #94a3b8;">
                    Votre sécurité est notre priorité ! 🔐
                </p>
                
                <p style="color: #64748b; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px;">
                    © 2025 SecureVault
                </p>
            </div>
        </body>
        </html>
        """
        
        self._send_email(email, subject, html_body)
    
    def _send_login_alert(self, email: str, username: str, device_info: str):
        """Send login alert for new device"""
        subject = "⚠️ Nouvelle connexion détectée"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0a1628; color: #e0e7ff; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a2942 0%, #0f1e36 100%); border-radius: 20px; padding: 40px; border: 1px solid rgba(239, 68, 68, 0.3);">
                <h2 style="color: #ef4444;">⚠️ Nouvelle connexion détectée</h2>
                
                <p style="color: #94a3b8; line-height: 1.6;">
                    Bonjour {username},<br><br>
                    Une connexion à votre compte SecureVault a été détectée depuis un nouvel appareil :
                </p>
                
                <div style="background-color: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; padding: 15px; margin: 20px 0;">
                    <p style="color: #fca5a5; margin: 0;">
                        <strong>Appareil:</strong> {device_info}<br>
                        <strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
                    </p>
                </div>
                
                <p style="color: #94a3b8; line-height: 1.6;">
                    Si ce n'était pas vous, <strong style="color: #ef4444;">changez immédiatement votre mot de passe</strong>.
                </p>
                
                <p style="color: #64748b; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px;">
                    © 2025 SecureVault
                </p>
            </div>
        </body>
        </html>
        """
        
        self._send_email(email, subject, html_body)
    
    def _send_email(self, to_email: str, subject: str, html_body: str):
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(html_body, 'html'))
            
            if self.email_config['smtp_port'] == 465:
                # SSL
                with smtplib.SMTP_SSL(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                    server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                    server.send_message(msg)
            else:
                # TLS
                with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                    server.starttls()
                    server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                    server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
