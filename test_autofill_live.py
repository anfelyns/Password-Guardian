
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.gui.autofill import open_and_type_credentials

print("="*70)
print("🧪 TEST LIVE DE L'AUTO-FILL")
print("="*70)

# Test avec Google (safe pour tester)
test_url = "https://www.instagram.com"
test_username = "iv.nees"
test_password = "Test@Pass123!#$"

print(f"\n📝 Configuration du test:")
print(f"   URL: {test_url}")
print(f"   Username: {test_username}")
print(f"   Password: {test_password}")

print(f"\n⚠️  CE TEST VA:")
print(f"   1. Ouvrir instagram dans votre navigateur par défaut")
print(f"   2. Taper le username dans la recherche")
print(f"   3. Appuyer sur TAB")
print(f"   4. Taper le password")
print(f"   5. Appuyer sur ENTER")

response = input("\n➡️  Continuer? (y/n): ").strip().lower()

if response == 'y':
    print("\n🚀 Lancement du test...")
    print("⏳ NE TOUCHEZ PAS AU CLAVIER/SOURIS!\n")
    
    success = open_and_type_credentials(
        url=test_url,
        username=test_username,
        password=test_password,
        delay=5.0
    )
    
    if success:
        print("\n✅ TEST TERMINÉ!")
        print("\n❓ Vérifiez dans Google:")
        print(f"   • Vous devriez voir '{test_username}' dans la recherche")
        print(f"   • Ou une page de résultats")
    else:
        print("\n❌ TEST ÉCHOUÉ - Voir les erreurs ci-dessus")
else:
    print("\n❌ Test annulé")

print("\n" + "="*70)
