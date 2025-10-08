from db import get_db_connection

try:
    # connexion a la base de donnees
    conn = get_db_connection()
    cursor = conn.cursor()

    #execution de la requete pour lister les tables 
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    #affichage des resultats
    print(" Connection réussie à la base de données !")
    print(" Tables trouvées :", tables)
    #fermeture propre des ressources
    cursor.close()
    conn.close()

except Exception as e:
    print(" Erreur de connexion :", e)
