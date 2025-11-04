from db import get_db_connection

try:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print(" Connection réussie à la base de données !")
    print(" Tables trouvées :", tables)
    cursor.close()
    conn.close()

except Exception as e:
    print(" Erreur de connexion :", e)
