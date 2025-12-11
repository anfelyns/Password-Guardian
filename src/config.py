# -*- coding: utf-8 -*-

import os
from datetime import timedelta

class Config:
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_NAME = 'password_guardian'
    
    SECRET_KEY = os.urandom(32)
    SESSION_LIFETIME = timedelta(hours=2)
    
    ENCRYPTION_KEY = b'votre_cle_de_chiffrement_32_bytes_ici!!'
    API_BASE_URL = "http://127.0.0.1:5000"
