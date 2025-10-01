import mysql.connector
from mysql.connector import Error

def test_mysql_passwords():
    print("🔍 Test des mots de passe MySQL XAMPP (port 1234)...")
    
    # Tous les mots de passe courants de XAMPP
    passwords_to_try = [
        '',            # Vide
        'root',        # Très courant
        'password',    # Anglais
        '1234',        # Simple
        'admin',       # Parfois utilisé
    ]
    
    for password in passwords_to_try:
        try:
            print(f"🔧 Essai avec mot de passe: '{password}'")
            
            config = {
                'host': 'localhost',
                'user': 'root',
                'password': password,
                'database': 'password_guardian',
                'port': 1234,  # ⬅️ PORT CORRECT
                'charset': 'utf8mb4'
            }
            
            conn = mysql.connector.connect(**config)
            
            print(f"🎉 SUCCÈS ! Mot de passe trouvé: '{password}'")
            
            # Vérifier les tables
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"📊 Tables trouvées : {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")
            
            cursor.close()
            conn.close()
            
            # Mettre à jour database_manager.py
            update_database_manager(password)
            return True
            
        except Error as e:
            error_msg = str(e)
            if "1045" in error_msg:
                print(f"❌ Accès refusé avec '{password}'")
            else:
                print(f"❌ Autre erreur avec '{password}': {error_msg}")
    
    print("\n💡 Solution : Réinitialiser le mot de passe")
    print("1. Arrête MySQL dans XAMPP")
    print("2. Clique sur 'Shell'")
    print("3. Exécute: mysqladmin -u root password \"newpassword\"")
    return False

def update_database_manager(password):
    """Mettre à jour le fichier database_manager.py avec le bon port et mot de passe"""
    try:
        with open('src/database/database_manager.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remplacer le mot de passe ET ajouter le port
        new_content = content.replace(
            "password='password123'", 
            f"password='{password}', port=1234"
        )
        
        with open('src/database/database_manager.py', 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print(f"✅ DatabaseManager mis à jour : port=1234, password='{password}'")
        
    except Exception as e:
        print(f"❌ Erreur mise à jour: {e}")

if __name__ == "__main__":
    test_mysql_passwords()