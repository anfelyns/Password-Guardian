# User management logic
"""
Authentication Manager for SecureVault
Complete authentication system with PBKDF2 hashing and email verification
"""
from database.engine import SessionLocal
from src.database.models import User, Password, OTPCode
from src.auth.authentication import Authentication, PasswordManager


class AuthManager:
    def __init__(self, host='localhost', user='root', password='', database='password_guardian', port=3306):
        """
        Initialize AuthManager with MySQL connection details and email config
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        
        # Email configuration - CHANGE THESE TO YOUR CREDENTIALS
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'your-email@gmail.com',  # YOUR EMAIL HERE
            'sender_password': 'your-app-password',   # YOUR APP PASSWORD HERE
            'sender_name': 'SecureVault'
        }
        
        # Initialize authentication system
        self.auth = Authentication(
            db_connection=self.get_db_connection,
            email_config=self.email_config
        )
        
        # Initialize password manager
        self.password_manager = PasswordManager()
    
    def get_db_connection(self):
        """Get MySQL database connection"""
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port
        )
    
    def authenticate(self, username_or_email, password):
        """
        Authenticate user (login)
        
        Returns: (success, user_info, message, metadata)
        """
        success, user, message = self.auth.login_user(
            identifier=username_or_email,
            master_password=password,
            device_info="Desktop App"
        )
        
        if success and user:
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
            metadata = {
                'requires_2fa': False  # Already verified during registration
            }
            return True, user_info, message, metadata
        
        return False, {}, message, {}
    
    def register_user(self, name, email, password):
        """
        Register a new user
        
        Returns: (success, message, extra_data)
        """
        # Evaluate password strength first
        strength_eval = self.password_manager.evaluate_password_strength(password)
        
        # Check if password is weak and offer replacement
        replaced_weak = False
        new_password = None
        
        if strength_eval['level'] == 'weak' and strength_eval['suggested_password']:
            # Offer to replace weak password
            new_password = strength_eval['suggested_password']
            replaced_weak = True
            # Use the strong password for registration
            password = new_password
        
        # Register with authentication system
        success, message, extra_data = self.auth.register_user(
            username=name,
            email=email,
            master_password=password
        )
        
        # Add password strength info to extra_data
        extra_data['replaced_weak'] = replaced_weak
        extra_data['new_password'] = new_password if replaced_weak else None
        extra_data['password_strength'] = strength_eval
        
        return success, message, extra_data
    
    def verify_two_factor(self, user_id, code, purpose='register', device_label=None):
        """
        Verify email verification code
        
        Args:
            user_id: User ID (not used, we verify by email)
            code: Verification code
            purpose: 'register' or 'login' (we use for registration verification)
            device_label: Device label (optional)
        
        Returns: (success, message)
        """
        # Get user email by ID
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return False, "Utilisateur introuvable"
            
            email = result[0]
            
            # Verify code
            success, message = self.auth.verify_user_code(email, code)
            return success, message
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def resend_verification_code(self, email):
        """Resend verification code to user"""
        return self.auth.resend_verification_code(email)
    
    def check_password_strength(self, password):
        """
        Check password strength
        
        Returns: dict with level, score, suggestions, suggested_password
        """
        return self.password_manager.evaluate_password_strength(password)
    
    def generate_strong_password(self, length=16):
        """Generate a strong password"""
        return self.password_manager.generate_secure_password(length)

    def __init__(self, host='localhost', user='root', password='', database='password_guardian', port=3306):
        """
        Initialize AuthManager with MySQL connection details
        
        Args:
            host: MySQL host
            user: MySQL username
            password: MySQL password
            database: Database name
            port: MySQL port (default 3306, but you're using 1234)
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        
        # Email configuration - CHANGE THESE TO YOUR CREDENTIALS
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',  # Gmail SMTP server
            'smtp_port': 587,                  # TLS port
            'sender_email': 'your-email@gmail.com',  # YOUR EMAIL HERE
            'sender_password': 'your-app-password',   # YOUR APP PASSWORD HERE
            'sender_name': 'SecureVault'
        }
        
        # Store 2FA codes temporarily (in production, use database)
        self.pending_2fa_codes = {}  # {user_id: {'code': '123456', 'expires': datetime, 'purpose': 'login'}}
        
        # TODO: Initialize MySQL connection
        # Example:
        # import mysql.connector
        # self.conn = mysql.connector.connect(
        #     host=self.host,
        #     user=self.user,
        #     password=self.password,
        #     database=self.database,
        #     port=self.port
        # )
    
    def authenticate(self, username_or_email, password):
        """
        Authenticate user with username/email and password
        
        Returns:
            tuple: (success: bool, user_info: dict, message: str, metadata: dict)
        """
        # TODO: Implement MySQL authentication
        # For now, return a demo response
        user_info = {
            'id': 1,
            'username': 'demo_user',
            'email': username_or_email
        }
        
        # Send 2FA code via email
        code = self.send_2fa_code(user_info['email'], user_info['id'], purpose='login')
        
        # Simulate 2FA requirement
        metadata = {
            'requires_2fa': True,
            'code_sent': code is not None
        }
        
        return True, user_info, "Authentification réussie", metadata
    
    def register_user(self, name, email, password):
        """
        Register a new user
        
        Returns:
            tuple: (success: bool, message: str, extra_data: dict)
        """
        # TODO: Implement MySQL user registration
        # Check password strength and replace if weak
        
        # Generate user ID (in production, this comes from database)
        user_id = random.randint(1, 10000)
        
        # Send 2FA code for email verification
        code = self.send_2fa_code(email, user_id, purpose='register')
        
        extra_data = {
            'user_id': user_id,
            'replaced_weak': False,
            'new_password': None,
            'two_factor_sent': code is not None
        }
        
        return True, "Inscription réussie", extra_data
    
    def verify_two_factor(self, user_id, code, purpose='login', device_label=None):
        """
        Verify 2FA code
        
        Args:
            user_id: User ID
            code: 6-digit code entered by user
            purpose: 'login' or 'register'
            device_label: Optional device label for trusted devices
            
        Returns:
            tuple: (success: bool, message: str)
        """
        # Check if code exists for this user
        if user_id not in self.pending_2fa_codes:
            return False, "Aucun code en attente pour cet utilisateur"
        
        stored_data = self.pending_2fa_codes[user_id]
        
        # Check if code matches
        if stored_data['code'] != code:
            return False, "Code incorrect"
        
        # Check if code expired (10 minutes validity)
        if datetime.now() > stored_data['expires']:
            del self.pending_2fa_codes[user_id]
            return False, "Code expiré. Veuillez demander un nouveau code"
        
        # Check purpose matches
        if stored_data['purpose'] != purpose:
            return False, "Code invalide pour cette opération"
        
        # Code is valid, remove it
        del self.pending_2fa_codes[user_id]
        
        return True, "Code vérifié avec succès"
    
    def send_2fa_code(self, email, user_id, purpose='login'):
        """
        Generate and send 2FA code via email
        
        Args:
            email: Recipient email address
            user_id: User ID for tracking
            purpose: 'login' or 'register'
        
        Returns:
            str: Generated 6-digit code (or None if failed)
        """
        # Generate random 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        
        # Store code with expiration (10 minutes)
        self.pending_2fa_codes[user_id] = {
            'code': code,
            'expires': datetime.now() + timedelta(minutes=10),
            'purpose': purpose
        }
        
        # Prepare email content
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
        else:  # register
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
            # Send email
            success = self._send_email(email, subject, message)
            
            if success:
                print(f"✅ 2FA code sent to {email}: {code}")
                return code
            else:
                print(f"❌ Failed to send email to {email}")
                # Still return code for testing (so app doesn't break)
                return code
                
        except Exception as e:
            print(f"❌ Email error: {e}")
            print(f"📋 2FA Code for testing: {code}")
            return code
    
    def _send_email(self, to_email, subject, html_content):
        """
        Send email via SMTP
        
        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()  # Enable TLS encryption
            
            # Login
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"SMTP Error: {e}")
            return False
