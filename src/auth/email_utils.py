# src/auth/email_utils.py
import os, smtplib, ssl, threading
from email.message import EmailMessage

def _smtp_conf():
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "465")),  # 465 SSL / 587 STARTTLS
        "user": os.environ.get("SMTP_USER"),
        "password": os.environ.get("SMTP_PASS"),
        "sender": os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER"),
        "use_ssl": os.environ.get("SMTP_USE_SSL", "1") == "1",
    }

def send_email(to: str, subject: str, body: str) -> bool:
    cfg = _smtp_conf()
    if not all([cfg["host"], cfg["port"], cfg["user"], cfg["password"], cfg["sender"]]):
        print("[EMAIL] Missing SMTP configuration in environment variables.")
        return False

    try:
        msg = EmailMessage()
        msg["From"] = cfg["sender"]
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        if cfg["use_ssl"]:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=context, timeout=15) as server:
                server.login(cfg["user"], cfg["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.login(cfg["user"], cfg["password"])
                server.send_message(msg)

        print(f"[EMAIL] Sent to {to} ({subject})")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

def send_email_async(*args, **kwargs):
    t = threading.Thread(target=send_email, args=args, kwargs=kwargs, daemon=True)
    t.start()
