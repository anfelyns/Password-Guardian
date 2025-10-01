# Database manager functions
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

class MySQLDatabaseManager:
    def __init__(self, host='localhost', user='root', password='', database='password_guardian', port=1234):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port,
            'charset': 'utf8mb4'
        }
    def get_connection(self):
        """Établir une connexion à la base MySQL"""
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Error as e:
            print(f"Erreur de connexion MySQL: {e}")
            return None
    
    # CRUD Utilisateurs
    def user_exists(self, username, email):
        """Vérifier si un utilisateur existe"""
        connection = self.get_connection()
        if not connection:
            return False
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (username, email)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            connection.close()
    
    def create_user(self, username, email, password_hash, salt):
        """Créer un nouvel utilisateur"""
        connection = self.get_connection()
        if not connection:
            return None
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (%s, %s, %s, %s)",
                (username, email, password_hash, salt)
            )
            connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Erreur création utilisateur: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def get_user_by_username(self, username):
        """Récupérer un utilisateur par son nom d'utilisateur"""
        connection = self.get_connection()
        if not connection:
            return None
            
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
    
    # CRUD Mots de passe
    def get_user_passwords(self, user_id, category=None):
        """Récupérer les mots de passe d'un utilisateur"""
        connection = self.get_connection()
        if not connection:
            return []
            
        try:
            cursor = connection.cursor(dictionary=True)
            if category and category != "all":
                cursor.execute(
                    "SELECT * FROM passwords WHERE user_id = %s AND category = %s ORDER BY site_name",
                    (user_id, category)
                )
            else:
                cursor.execute(
                    "SELECT * FROM passwords WHERE user_id = %s ORDER BY site_name",
                    (user_id,)
                )
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()
    
    def add_password(self, password_data):
        """Ajouter un nouveau mot de passe"""
        connection = self.get_connection()
        if not connection:
            return None
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                """INSERT INTO passwords 
                (user_id, site_name, site_icon, username, encrypted_password, category, strength, favorite)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    password_data['user_id'],
                    password_data['site_name'],
                    password_data.get('site_icon', '🔐'),
                    password_data['username'],
                    password_data['encrypted_password'],
                    password_data.get('category', 'personal'),
                    password_data.get('strength', 'medium'),
                    password_data.get('favorite', False)
                )
            )
            connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Erreur ajout mot de passe: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    # Gestion des sessions
    def create_session(self, user_id, token, expires_at):
        """Créer une nouvelle session"""
        connection = self.get_connection()
        if not connection:
            return None
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user_id, token, expires_at)
            )
            connection.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            connection.close()
    
    def get_session(self, token):
        """Récupérer une session par son token"""
        connection = self.get_connection()
        if not connection:
            return None
            
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM sessions WHERE token = %s", (token,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
    
    # Journal d'activité
    def log_activity(self, user_id, action, details=None):
        """Journaliser une activité"""
        connection = self.get_connection()
        if not connection:
            return
            
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO activity_logs (user_id, action, details) VALUES (%s, %s, %s)",
                (user_id, action, details)
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()