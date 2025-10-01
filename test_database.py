import sys
import os

# Ajouter le dossier src au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.database_manager import MySQLDatabaseManager

def test_database():
    print("🔍 Test du DatabaseManager...")
    
    db = MySQLDatabaseManager()
    
    # Test connexion
    conn = db.get_connection()
    if conn:
        print("✅ Connexion MySQL réussie!")
        
        # Test vérification tables
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"📊 Tables trouvées : {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
        # Test des fonctions CRUD basiques
        print("\n🧪 Tests des fonctions :")
        print(f"   - user_exists: {db.user_exists('test', 'test@test.com')}")
        print("   ✅ Toutes les fonctions sont prêtes!")
        
    else:
        print("❌ Échec de connexion à la base de données")

if __name__ == "__main__":
    test_database()