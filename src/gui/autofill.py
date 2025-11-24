# src/gui/autofill.py - MÉTHODE AVEC CLICS (PLUS FIABLE)
import time
import webbrowser
import pyautogui
import pyperclip


def open_and_type_credentials(url: str, username: str, password: str, delay: float = 6.0):
    """
    NOUVELLE MÉTHODE: Attend que l'utilisateur clique lui-même sur les champs.
    Plus fiable car évite les problèmes de focus et de timing.
    """
    if not url:
        print("❌ URL manquante")
        return False

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"\n{'='*70}")
    print(f"🚀 AUTO-FILL AVEC ASSISTANCE MANUELLE")
    print(f"{'='*70}")
    print(f"🌐 URL: {url}")
    print(f"👤 Username: {username}")
    print(f"🔒 Password: {'*' * len(password)}")
    
    try:
        # Sauvegarder le presse-papiers
        original_clipboard = ""
        try:
            original_clipboard = pyperclip.paste()
        except:
            pass
        
        # 1. Ouvrir le navigateur
        print(f"\n📂 ÉTAPE 1: Ouverture du site")
        print(f"   Ouverture de: {url}")
        webbrowser.open(url)
        
        print(f"\n⏳ Attente de {delay} secondes...")
        for i in range(int(delay), 0, -1):
            print(f"   {i}...", end='\r', flush=True)
            time.sleep(1)
        print(f"   ✅ Page chargée!          ")
        
        # 2. IDENTIFIANT - avec notification sonore
        print(f"\n{'='*70}")
        print(f"📧 ÉTAPE 2: SAISIE DE L'IDENTIFIANT")
        print(f"{'='*70}")
        print(f"\n   ⏸️  ACTION REQUISE:")
        print(f"   1. 🖱️  Cliquez sur le champ EMAIL/USERNAME")
        print(f"   2. ⌨️  Puis appuyez sur ENTRÉE dans cette console")
        print(f"\n   L'identifiant sera automatiquement collé")
        print(f"{'='*70}")
        
        input("\n   👉 Appuyez sur ENTRÉE quand vous êtes prêt...")
        
        # Copier et coller l'identifiant
        pyperclip.copy(username)
        time.sleep(0.3)
        
        print(f"\n   📋 Collage de l'identifiant...")
        # Vider d'abord le champ
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        # Coller
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        
        print(f"   ✅ Identifiant collé: {username}")
        
        # 3. MOT DE PASSE - avec notification
        print(f"\n{'='*70}")
        print(f"🔒 ÉTAPE 3: SAISIE DU MOT DE PASSE")
        print(f"{'='*70}")
        print(f"\n   ⏸️  ACTION REQUISE:")
        print(f"   1. 🖱️  Cliquez sur le champ MOT DE PASSE")
        print(f"   2. ⌨️  Puis appuyez sur ENTRÉE dans cette console")
        print(f"\n   Le mot de passe sera automatiquement collé")
        print(f"{'='*70}")
        
        input("\n   👉 Appuyez sur ENTRÉE quand vous êtes prêt...")
        
        # Copier et coller le mot de passe
        pyperclip.copy(password)
        time.sleep(0.3)
        
        print(f"\n   📋 Collage du mot de passe...")
        # Vider d'abord le champ
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        # Coller
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        
        print(f"   ✅ Mot de passe collé ({len(password)} caractères)")
        
        # 4. Soumission
        print(f"\n{'='*70}")
        print(f"📨 ÉTAPE 4: SOUMISSION")
        print(f"{'='*70}")
        
        response = input("\n   Soumettre automatiquement? (y/n): ").strip().lower()
        
        if response == 'y':
            print(f"\n   ⏎  Appui sur ENTER...")
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)
            print(f"   ✅ Formulaire soumis!")
        else:
            print(f"\n   ℹ️  Cliquez manuellement sur 'Se connecter'")
        
        # Restaurer le presse-papiers
        if original_clipboard:
            try:
                pyperclip.copy(original_clipboard)
            except:
                pass
        
        print(f"\n{'='*70}")
        print(f"✅ AUTO-FILL TERMINÉ!")
        print(f"{'='*70}\n")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Processus interrompu par l'utilisateur")
        return False
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ ERREUR")
        print(f"{'='*70}")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*70}\n")
        return False


def open_and_type_credentials_auto(url: str, username: str, password: str, delay: float = 7.0):
    """
    MÉTHODE 100% AUTOMATIQUE (peut ne pas fonctionner sur tous les sites)
    Utilise des pauses plus longues pour éviter les problèmes de timing.
    """
    if not url:
        return False

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"\n{'='*70}")
    print(f"🚀 AUTO-FILL AUTOMATIQUE")
    print(f"{'='*70}")
    
    try:
        # Sauvegarder clipboard
        original_clipboard = pyperclip.paste() if pyperclip.paste() else ""
        
        # Ouvrir le site
        print(f"📂 Ouverture: {url}")
        webbrowser.open(url)
        
        # Attente longue pour le chargement
        print(f"⏳ Attente de {delay} secondes...")
        time.sleep(delay)
        
        # Focus sur la fenêtre
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height // 2)
        time.sleep(1.5)
        
        # IDENTIFIANT
        print(f"\n📧 Saisie de l'identifiant...")
        pyperclip.copy(username)
        time.sleep(0.5)
        
        # S'assurer que le champ est vide
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.press('delete')
        time.sleep(0.3)
        
        # Coller
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.0)  # Pause plus longue
        print(f"   ✅ Identifiant: {username}")
        
        # Passer au champ suivant avec une longue pause
        print(f"\n⏭️  Passage au mot de passe...")
        pyautogui.press('tab')
        time.sleep(1.5)  # Pause TRÈS longue
        
        # MOT DE PASSE
        print(f"\n🔒 Saisie du mot de passe...")
        pyperclip.copy(password)
        time.sleep(0.5)
        
        # Vider le champ
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.press('delete')
        time.sleep(0.3)
        
        # Coller
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.0)
        print(f"   ✅ Mot de passe saisi ({len(password)} caractères)")
        
        # Soumettre
        print(f"\n📨 Soumission...")
        time.sleep(1.0)
        pyautogui.press('enter')
        
        # Restaurer clipboard
        pyperclip.copy(original_clipboard)
        
        print(f"\n✅ Terminé!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False


def simple_copy_paste_method(url: str, username: str, password: str):
    """
    MÉTHODE LA PLUS SIMPLE: Juste copier les infos, l'utilisateur colle.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    print(f"\n{'='*70}")
    print(f"📋 MÉTHODE COPIER-COLLER SIMPLE")
    print(f"{'='*70}")
    
    webbrowser.open(url)
    print(f"✅ Site ouvert: {url}\n")
    
    time.sleep(3)
    
    # Copier l'identifiant
    pyperclip.copy(username)
    print(f"📧 IDENTIFIANT COPIÉ: {username}")
    print(f"   👉 Collez-le dans le champ avec Ctrl+V")
    input(f"   Appuyez sur ENTRÉE quand c'est fait...\n")
    
    # Copier le mot de passe
    pyperclip.copy(password)
    print(f"🔒 MOT DE PASSE COPIÉ (longueur: {len(password)})")
    print(f"   👉 Collez-le dans le champ avec Ctrl+V")
    input(f"   Appuyez sur ENTRÉE quand c'est fait...\n")
    
    print(f"✅ Vous pouvez maintenant cliquer sur 'Se connecter'")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    print("🧪 TEST DES MÉTHODES AUTO-FILL")
    print("="*70)
    print("\nMéthodes disponibles:")
    print("1. Assistée (recommandée) - Vous cliquez, on colle")
    print("2. Automatique - Tout automatique avec longues pauses")
    print("3. Simple - Juste copie dans le presse-papiers")
    
    choice = input("\nChoisissez (1/2/3): ").strip()
    
    test_url = "https://www.google.com"
    test_user = "test_user_123"
    test_pass = "Test@Pass123!#$"
    
    if choice == "1":
        open_and_type_credentials(test_url, test_user, test_pass, delay=5.0)
    elif choice == "2":
        open_and_type_credentials_auto(test_url, test_user, test_pass, delay=7.0)
    elif choice == "3":
        simple_copy_paste_method(test_url, test_user, test_pass)
    else:
        print("❌ Choix invalide")