"""
Authentication Manager for SecureVault
Handles user authentication, registration, and 2FA
"""
import random, string, smtplib
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
        # Demo only: accept any password for this demo user
        user_info = {'id': 1, 'username': 'demo_user', 'email': username_or_email}
        code = self.send_2fa_code(user_info['email'], user_info['id'], purpose="login")
        return {"user": user_info, "2fa_sent": True, "code_debug": code}  # show code for testing

    def _gen_code(self, n=6):
        return ''.join(random.choice(string.digits) for _ in range(n))

    def send_2fa_code(self, to_email, user_id, purpose="login"):
        code = self._gen_code()
        self.pending_2fa_codes[user_id] = {"code": code, "expires": datetime.utcnow() + timedelta(minutes=10)}
        # send email
        msg = MIMEMultipart()
        msg['From'] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
        msg['To'] = to_email
        msg['Subject'] = "Your SecureVault 2FA Code"
        msg.attach(MIMEText(f"Your verification code is: {code}\nIt expires in 10 minutes.", 'plain'))

        try:
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print("Email error:", e)
        return code

    def verify_2fa(self, user_id, code):
        entry = self.pending_2fa_codes.get(user_id)
        if not entry: return False
        if datetime.utcnow() > entry['expires']: return False
        return entry['code'] == code
