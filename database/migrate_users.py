# -*- coding: utf-8 -*-
# migrate_users.py - Migrer les utilisateurs existants
import mysql.connector
import hashlib
import os

def migrate_existing_users():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="inessouai2005_",
        database="password_guardian",
        port=3306
    )
    
    cursor = conn.cursor(dictionary=True)
    
    # Vérifier s'il y a des utilisateurs dans la table
    cursor.execute("SELECT * FROM users LIMIT 1")
    existing_users = cursor.fetchall()
    
    if not existing_users:
        print("📝 Aucun utilisateur existant trouvé. Les nouveaux utilisateurs seront créés normalement.")
    else:
        print(f"✅ {len(existing_users)} utilisateur(s) trouvé(s) dans la base")
        for user in existing_users:
            print(f"   - {user['username']} ({user['email']})")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    migrate_existing_users()