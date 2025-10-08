"""
Authentication Manager for SecureVault
Handles user authentication, registration, and 2FA
"""
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta


class AuthManager:
    def __init__(self, host='localhost', user='root', password='', database='password_guardian', port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port

        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'hhhhhhhhhhhh12hhhh@gmail.com',
            'sender_password': '123456789',
            'sender_name': 'SecureVault'
        }

        self.pending_2fa_codes = {}

    def authenticate(self, username_or_email, password):
        user_info = {
            'id': 1,
            'username': 'demo_user',
            'email': username_or_email
        }

        code = self.send_2fa_code(user_info['email'], user_info['id'], purpose='login')

        metadata = {
            'requires_2fa': True,
            'code_sent': code is not None
        }

        return True, user_info, "Authentification réussie", metadata

    def register_user(self, name, email, password):
        user_id = random.randint(1, 10000)

        code = self.send_2fa_code(email, user_id, purpose='register')

        extra_data = {
            'user_id': user_id,
            'replaced_weak': False,
            'new_password': None,
            'two_factor_sent': code is not None
        }

        return True, "Inscription réussie", extra_data

    def verify_two_factor(self, user_id, code, purpose='login', device_label=None):
        if user_id not in self.pending_2fa_codes:
            return False, "Aucun code en attente pour cet utilisateur"

        stored_data = self.pending_2fa_codes[user_id]

        if stored_data['code'] != code:
            return False, "Code incorrect"

        if datetime.now() > stored_data['expires']:
            del self.pending_2fa_codes[user_id]
            return False, "Code expiré. Veuillez demander un nouveau code"

        if stored_data['purpose'] != purpose:
            return False, "Code invalide pour cette opération"

        del self.pending_2fa_codes[user_id]

        return True, "Code vérifié avec succès"

    def send_2fa_code(self, email, user_id, purpose='login'):
        code = ''.join(random.choices(string.digits, k=6))

        self.pending_2fa_codes[user_id] = {
            'code': code,
            'expires': datetime.now() + timedelta(minutes=10),
            'purpose': purpose
        }

        if purpose == 'login':
            subject = "🔐 Code de connexion SecureVault"
            message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #0a1628; color: #e0e7ff; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a2942 0%, #0f1e36 100%); border-radius: 20px; padding: 40px; border: 1px solid rgba(96, 165, 250, 0.2);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #60a5fa; margin: 0;">🛡️ SecureVault</h1>
                        <p style="color: #94a3b8; margin-top: 10px;">Votre gestionnaire de mots de passe sécurisé</p>
                    </div>
                    
                    <h2 style="color: #e0e7ff; margin-bottom: 20px;">Code de vérification</h2>
                    
                    <p style="color: #94a3b8; line-height: 1.6;">
                        Bonjour,<br><br>
                        Vous avez demandé à vous connecter à votre compte SecureVault. 
                        Voici votre code de vérification :
                    </p>
                    
                    <div style="background-color: rgba(59, 130, 246, 0.1); border: 2px solid #3b82f6; border-radius: 15px; padding: 30px; text-align: center; margin: 30px 0;">
                        <p style="color: #94a3b8; margin: 0 0 15px 0; font-size: 14px;">Code de vérification</p>
                        <p style="font-size: 42px; font-weight: bold; color: #60a5fa; letter-spacing: 8px; margin: 0; font-family: 'Courier New', monospace;">
                            {code}
                        </p>
                    </div>
                    
                    <p style="color: #94a3b8; line-height: 1.6;">
                        Ce code est valide pendant <strong style="color: #e0e7ff;">10 minutes</strong>.
                    </p>
                    
                    <div style="background-color: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; padding: 15px; margin-top: 25px; border-radius: 5px;">
                        <p style="color: #fca5a5; margin: 0; font-size: 13px;">
                            <strong>⚠️ Sécurité :</strong> Si vous n'avez pas demandé ce code, ignorez cet email et assurez-vous que votre compte est sécurisé.
                        </p>
                    </div>
                    
                    <p style="color: #64748b; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px;">
                        © 2025 SecureVault - Gestionnaire de mots de passe sécurisé
                    </p>
                </div>
            </body>
            </html>
            """
        else:
            subject = "✨ Bienvenue sur SecureVault - Vérifiez votre email"
            message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #0a1628; color: #e0e7ff; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a2942 0%, #0f1e36 100%); border-radius: 20px; padding: 40px; border: 1px solid rgba(96, 165, 250, 0.2);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #60a5fa; margin: 0;">🛡️ SecureVault</h1>
                        <p style="color: #94a3b8; margin-top: 10px;">Votre gestionnaire de mots de passe sécurisé</p>
                    </div>
                    
                    <h2 style="color: #e0e7ff; margin-bottom: 20px;">🎉 Bienvenue !</h2>
                    
                    <p style="color: #94a3b8; line-height: 1.6;">
                        Merci de vous être inscrit sur SecureVault !<br><br>
                        Pour activer votre compte et commencer à protéger vos mots de passe, 
                        veuillez vérifier votre adresse email avec le code ci-dessous :
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
                    
                    <div style="background-color: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; padding: 15px; margin-top: 25px; border-radius: 5px;">
                        <p style="color: #94a3b8; margin: 0; font-size: 13px;">
                            <strong>💡 Conseil :</strong> Avec SecureVault, vous pouvez stocker et gérer tous vos mots de passe en toute sécurité !
                        </p>
                    </div>
                    
                    <p style="color: #64748b; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px;">
                        © 2025 SecureVault - Gestionnaire de mots de passe sécurisé
                    </p>
                </div>
            </body>
            </html>
            """

        try:
            success = self._send_email(email, subject, message)

            if success:
                print(f"✅ 2FA code sent to {email}: {code}")
                return code
            else:
                print(f"❌ Failed to send email to {email}")
                return code

        except Exception as e:
            print(f"❌ Email error: {e}")
            print(f"📋 2FA Code for testing: {code}")
            return code

    def _send_email(self, to_email, subject, html_content):
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()

            server.login(self.email_config['sender_email'], self.email_config['sender_password'])

            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            print(f"SMTP Error: {e}")
            return False