import mysql.connector
from mysql.connector import Error
from datetime import datetime


class MySQLDatabaseManager:
    """
    Centralise toutes les opérations MySQL pour Password Guardian :
    - Connexion / création de tables
    - Gestion des utilisateurs
    - Codes 2FA
    - Historique d’activités
    - Appareils utilisateurs
    """

    def __init__(self, host, user, password, database, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port

        self.create_tables_if_not_exist()


    def get_connection(self):
        """Retourne un objet connexion MySQL valide ou None."""
        try:
            con = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            if con.is_connected():
                return con
        except Error as e:
            print(f"[DB ERROR] Connection failed: {e}")
            return None

    def user_exists(self, username, email):
        """Vérifie si un utilisateur existe déjà."""
        con = self.get_connection()
        if not con:
            return False
        cur = con.cursor()
        cur.execute(
            "SELECT id FROM users WHERE username=%s OR email=%s LIMIT 1",
            (username, email)
        )
        res = cur.fetchone()
        cur.close()
        con.close()
        return res is not None

    def create_user(self, username, password_hash, email, salt):
        """Crée un utilisateur dans la base."""
        con = self.get_connection()
        if not con:
            return None
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO users (username, password_hash, email, salt, created_at, email_verified)
                VALUES (%s, %s, %s, %s, NOW(), 0)
            """, (username, password_hash, email, salt))
            con.commit()
            user_id = cur.lastrowid
            return user_id
        except Error as e:
            print(f"[DB ERROR] create_user: {e}")
            con.rollback()
            return None
        finally:
            cur.close()
            con.close()

    def get_user_by_username(self, username):
        """Récupère un utilisateur à partir de son nom."""
        con = self.get_connection()
        if not con:
            return None
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s LIMIT 1", (username,))
        row = cur.fetchone()
        cur.close()
        con.close()
        return row


    def store_verification_code(self, user_id, code, purpose):
        """Insère un code 2FA pour l'utilisateur."""
        con = self.get_connection()
        if not con:
            return False
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO verification_codes (user_id, code, purpose, used, created_at, expires_at)
                VALUES (%s, %s, %s, 0, NOW(), DATE_ADD(NOW(), INTERVAL 10 MINUTE))
            """, (user_id, code, purpose))
            con.commit()
            return True
        except Error as e:
            print(f"[DB ERROR] store_verification_code: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()


    def log_activity(self, user_id, action):
        """Ajoute une entrée dans le journal d’activité."""
        con = self.get_connection()
        if not con:
            return False
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO activity_logs (user_id, action, timestamp)
                VALUES (%s, %s, NOW())
            """, (user_id, action))
            con.commit()
            return True
        except Error as e:
            print(f"[DB ERROR] log_activity: {e}")
            return False
        finally:
            cur.close()
            con.close()

    def register_device(self, user_id, fingerprint, label):
        """Ajoute ou met à jour un appareil utilisé par l’utilisateur."""
        con = self.get_connection()
        if not con:
            return False
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT id FROM user_devices WHERE user_id=%s AND fingerprint=%s
            """, (user_id, fingerprint))
            existing = cur.fetchone()

            if existing:
                cur.execute("""
                    UPDATE user_devices SET last_seen=NOW() WHERE id=%s
                """, (existing[0],))
            else:
                cur.execute("""
                    INSERT INTO user_devices (user_id, fingerprint, label, first_seen, last_seen)
                    VALUES (%s, %s, %s, NOW(), NOW())
                """, (user_id, fingerprint, label))
            con.commit()
            return True
        except Error as e:
            print(f"[DB ERROR] register_device: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()


    def create_tables_if_not_exist(self):
        """Crée toutes les tables nécessaires si elles n’existent pas."""
        con = self.get_connection()
        if not con:
            print("[DB ERROR] Unable to connect to create tables.")
            return False
        cur = con.cursor()
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE,
                    email VARCHAR(200) UNIQUE,
                    password_hash TEXT,
                    salt TEXT,
                    email_verified BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME NULL
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS verification_codes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    code VARCHAR(10),
                    purpose VARCHAR(50),
                    used BOOLEAN DEFAULT 0,
                    created_at DATETIME,
                    expires_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    action VARCHAR(255),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_devices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    fingerprint VARCHAR(255),
                    label VARCHAR(255),
                    first_seen DATETIME,
                    last_seen DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            con.commit()
            print("✅ Database tables verified/created successfully.")
            return True

        except Error as e:
            print(f"[DB ERROR] create_tables_if_not_exist: {e}")
            return False

        finally:
            cur.close()
            con.close()
