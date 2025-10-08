
import os
from datetime import timedelta

class Config:
    # Base de données MySQL
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''  # Mettez votre mot de passe MySQL
    DB_NAME = 'password_guardian'
    
    # Sécurité
    SECRET_KEY = os.urandom(32)
    SESSION_LIFETIME = timedelta(hours=2)
    
    # Encryption
    ENCRYPTION_KEY = b'votre_cle_de_chiffrement_32_bytes_ici!!'
