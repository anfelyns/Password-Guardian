
from flask import Flask, request, jsonify
from db import get_db_connection
import random, string
from Crypto.Cipher import AES
import base64
import os  # For generating random bytes


app = Flask(__name__)

# ================== AES ENCRYPTION ==================

SECRET_KEY = b"1234567890123456"  # AES secret key (must be 16/24/32 bytes)

def encrypt_password(password: str) -> str:
    """Encrypt a password using AES (CBC mode) with random IV."""
    # Generate a NEW random IV each time
    IV = os.urandom(16)  # 16 random bytes
    
    # Create AES cipher in CBC mode with the IV
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    
    # Add padding to make password length multiple of 16
    padding_length = 16 - (len(password) % 16)
    password_padded = password + chr(padding_length) * padding_length
    
    # Encrypt the padded password
    encrypted = cipher.encrypt(password_padded.encode('utf-8'))
    
    # Combine IV and encrypted data for storage
    combined = IV + encrypted  # IV (16 bytes) + encrypted data
    return base64.b64encode(combined).decode('utf-8')

def decrypt_password(encrypted_password: str) -> str:
    """Decrypt an AES encrypted password."""
    # Decode from base64
    combined_bytes = base64.b64decode(encrypted_password)
    
    # Extract IV (first 16 bytes) and encrypted data
    IV = combined_bytes[:16]  # First 16 bytes = IV
    encrypted_data = combined_bytes[16:]  # Remaining bytes = encrypted data
    
    # Create AES cipher with the extracted IV
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    
    # Decrypt and decode to string
    decrypted = cipher.decrypt(encrypted_data).decode('utf-8')
    
    # Remove padding based on the last character
    padding_length = ord(decrypted[-1])
    return decrypted[:-padding_length]


# ================== HELPERS ==================

def check_password_strength(password: str) -> str:
    """Check password strength (weak, medium, strong)."""
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in string.punctuation for c in password)

    if length >= 12 and has_upper and has_digit and has_symbol:
        return "strong"
    elif length >= 8 and (has_digit or has_symbol):
        return "medium"
    else:
        return "weak"

def generate_strong_password(length=12):
    """Generate a password that is ALWAYS strong"""
    
    # Verification de la longueur minimale
    if length < 12:
        length = 12  # Force minimum 12 caracteres
    
    # Caracteres par categorie
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = string.punctuation
    
    # Garantir au moins 1 caractere de chaque type
    password = [
        random.choice(uppercase),  # Au moins 1 majuscule
        random.choice(digits),     # Au moins 1 chiffre
        random.choice(symbols),    # Au moins 1 symbole
    ]
    
    # Remplir le reste avec tous les caracteres melangs
    all_chars = lowercase + uppercase + digits + symbols
    for _ in range(length - 3):  # -3 car on a deja 3 caracteres
        password.append(random.choice(all_chars))
    
    # Melanger pour eviter un motif previsible
    random.shuffle(password)
    
    return ''.join(password)



# ================== START SERVER ==================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
