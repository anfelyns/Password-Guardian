"""
src/backend/api_client.py - FIXED Complete API Client
Le problème: Le mot de passe était chiffré 2 fois
Solution: Utiliser decrypt() au lieu d'encrypt() quand on récupère
"""
import requests
from typing import Dict, List, Tuple, Optional
from src.backend.encryption import EncryptionManager


class APIClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.encryption = EncryptionManager()
        print("✅ API Client initialized with encryption support")
    
    def _handle_response(self, response):
        """Handle API response"""
        try:
            if not response.content:
                return False, "Empty response", None
            
            data = response.json()
            
            if response.status_code >= 400:
                return False, data.get('error', 'Unknown error'), None
            
            if isinstance(data, list):
                return True, 'Success', data
            
            return True, data.get('message', 'Success'), data
            
        except Exception as e:
            print(f"❌ Response handling error: {e}")
            return False, f"Response error: {str(e)}", None
    
    
    def add_password(self, user_id: int, site_name: str, username: str, 
                     password: str, category: str, favorite: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """Add password (encrypted on client side)"""
        try:
            print(f"🔒 Encrypting password for '{site_name}'...")
            encrypted_password = self.encryption.encrypt(password)
            print(f"✅ Password encrypted: {len(encrypted_password)} chars")
            print(f"📝 Original password: {password}")
            print(f"🔐 Encrypted result: {encrypted_password[:50]}...")
            
            payload = {
                'user_id': user_id,
                'site_name': site_name,
                'username': username,
                'encrypted_password': encrypted_password,
                'category': category,
                'favorite': favorite
            }
            
            print(f"📤 Sending to API: {self.base_url}/passwords")
            response = self.session.post(f"{self.base_url}/passwords", json=payload)
            
            success, message, data = self._handle_response(response)
            
            if success:
                print(f"✅ Password added successfully for '{site_name}'")
            else:
                print(f"❌ Failed to add password: {message}")
            
            return success, message, data
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, None
    
    def get_passwords(self, user_id: int) -> Tuple[bool, str, Optional[List[Dict]]]:
        """Get all passwords for a user"""
        try:
            print(f"📥 Fetching passwords for user {user_id}...")
            response = self.session.get(f"{self.base_url}/passwords/{user_id}")
            
            print(f"📊 Response status: {response.status_code}")
            
            success, message, data = self._handle_response(response)
            
            if success:
                if isinstance(data, list):
                    print(f"✅ Retrieved {len(data)} passwords")
                    # ⭐ IMPORTANT: Les mots de passe sont déjà chiffrés dans la DB
                    # On ne fait RIEN ici, juste retourner les données
                    return True, message, data
                elif data is None or (isinstance(data, dict) and not data):
                    print("ℹ️ No passwords found (empty response)")
                    return True, "No passwords found", []
                else:
                    print(f"⚠️ Unexpected data type: {type(data)}")
                    return True, "No passwords found", []
            else:
                print(f"❌ API error: {message}")
                return False, message, []
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, []
    
    def update_password(self, password_id: int, site_name: str, username: str,
                       password: str, category: str, favorite: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """Update password"""
        try:
            print(f"🔒 Encrypting updated password for ID {password_id}...")
            
            # ⭐ IMPORTANT: Vérifier si le mot de passe est déjà chiffré
            # Si c'est déjà du base64, c'est qu'il est déjà chiffré
            if self._looks_encrypted(password):
                print(f"⚠️ Password already encrypted, using as-is")
                encrypted_password = password
            else:
                print(f"🔐 Encrypting new password...")
                encrypted_password = self.encryption.encrypt(password)
                print(f"✅ New password encrypted")
            
            payload = {
                'site_name': site_name,
                'username': username,
                'encrypted_password': encrypted_password,
                'category': category,
                'favorite': favorite
            }
            
            response = self.session.put(f"{self.base_url}/passwords/{password_id}", json=payload)
            success, message, data = self._handle_response(response)
            
            if success:
                print(f"✅ Password updated successfully")
            
            return success, message, data
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, None
    
    def delete_password(self, password_id: int, hard: bool = False) -> Tuple[bool, str]:
        """Delete password"""
        try:
            print(f"🗑️ Deleting password {password_id}...")
            response = self.session.delete(f"{self.base_url}/passwords/{password_id}")
            success, message, _ = self._handle_response(response)
            
            if success:
                print(f"✅ Password deleted successfully")
            
            return success, message
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def decrypt_password(self, encrypted_password: str) -> Optional[str]:
        """
        Decrypt password
        ⭐ CRITICAL: Cette méthode déchiffre le mot de passe stocké
        """
        try:
            if not encrypted_password:
                print("⚠️ Empty encrypted password")
                return ""
            
            print(f"🔓 Decrypting password...")
            print(f"📦 Encrypted (first 50 chars): {encrypted_password[:50]}...")
            
            # Déchiffrer avec notre EncryptionManager
            decrypted = self.encryption.decrypt(encrypted_password)
            
            print(f"✅ Decryption result: {decrypted}")
            
            # Vérifier si c'est un message d'erreur
            if decrypted.startswith('[DECRYPT_ERROR'):
                print(f"❌ Decryption failed: {decrypted}")
                return None
            
            return decrypted
            
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _looks_encrypted(self, text: str) -> bool:
        """Check if text looks like base64 encrypted data"""
        import re
        # Base64 pattern: letters, numbers, +, /, ending with = or ==
        pattern = r'^[A-Za-z0-9+/]+={0,2}$'
        return bool(re.match(pattern, text)) and len(text) > 20
    
    def restore_password(self, password_id: int, target_category: str = "personal") -> Tuple[bool, str]:
        """Restore password from trash"""
        try:
            response = self.session.put(
                f"{self.base_url}/passwords/{password_id}",
                json={'category': target_category}
            )
            success, message, _ = self._handle_response(response)
            return success, message
        except Exception as e:
            return False, str(e)
    
    def check_connection(self) -> bool:
        """Check if API is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=2)
            return response.status_code == 200
        except:
            return False



if __name__ == "__main__":
    print("🧪 Testing encryption/decryption...")
    
    client = APIClient()
    
    # Test password
    original = "MySecretPassword123!"
    print(f"\n📝 Original: {original}")
    
    # Encrypt
    encrypted = client.encryption.encrypt(original)
    print(f"🔐 Encrypted: {encrypted}")
    
    # Decrypt
    decrypted = client.decrypt_password(encrypted)
    print(f"🔓 Decrypted: {decrypted}")
    
    # Verify
    if original == decrypted:
        print("✅ SUCCESS: Encryption/Decryption works!")
    else:
        print("❌ FAILED: Mismatch!")
        print(f"   Expected: {original}")
        print(f"   Got: {decrypted}")