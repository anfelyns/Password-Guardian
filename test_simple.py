import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',      # Vide
        database='password_guardian',
        port=1234         # Port XAMPP
    )
    print("✅ CONNEXION DIRECTE RÉUSSIE !")
    conn.close()
except Exception as e:
    print(f"❌ Erreur directe: {e}")