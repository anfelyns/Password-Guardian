# -*- coding: utf-8 -*-
# src/backend/api_client.py - FIXED VERSION
import requests
from typing import Tuple, List, Dict, Any


class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:5000", timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    # ---------- PASSWORDS ----------
    def get_passwords(self, user_id: int) -> Tuple[bool, str, List[Dict[str, Any]]]:
        try:
            r = self.session.get(
                f"{self.base_url}/passwords/{user_id}",
                timeout=self.timeout,
            )
            if r.ok:
                return True, "ok", r.json()
            return False, f"{r.status_code}: {r.text}", []
        except Exception as e:
            return False, str(e), []

    def add_password(
        self,
        user_id: int,
        site_name: str,
        username: str,
        encrypted_password: str,  # This is actually plain password now
        category: str,
        site_url: str = "",
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Add a new password
        Note: 'encrypted_password' parameter is actually the PLAIN password
        Backend will encrypt it properly
        """
        try:
            # ✅ FIXED: Send 'password' key to backend (not 'encrypted_password')
            payload = {
                "user_id": user_id,
                "site_name": site_name,
                "site_url": site_url,
                "username": username,
                "password": encrypted_password,  # ✅ Changed key name to 'password'
                "category": category,
            }
            
            print(f"\n📤 API Client sending payload:")
            print(f"   URL: {self.base_url}/passwords")
            print(f"   Payload: {payload}")
            
            r = self.session.post(
                f"{self.base_url}/passwords",
                json=payload,
                timeout=self.timeout,
            )
            
            print(f"📥 API Response:")
            print(f"   Status: {r.status_code}")
            print(f"   Response: {r.text[:200]}")
            
            if r.ok:
                return True, "ok", r.json()
            else:
                error_msg = r.text
                try:
                    error_json = r.json()
                    error_msg = error_json.get('error', r.text)
                except:
                    pass
                return False, f"{r.status_code}: {error_msg}", {}
                
        except Exception as e:
            print(f"❌ API Client Exception: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e), {}

    def update_password(self, password_id: int, updates: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            # ✅ FIXED: If 'encrypted_password' in updates, rename to 'password'
            if 'encrypted_password' in updates:
                updates['password'] = updates.pop('encrypted_password')
            
            r = self.session.put(
                f"{self.base_url}/passwords/{password_id}",
                json=updates,
                timeout=self.timeout,
            )
            if r.ok:
                return True, "ok"
            return False, f"{r.status_code}: {r.text}"
        except Exception as e:
            return False, str(e)

    def trash_password(self, password_id: int) -> Tuple[bool, str]:
        try:
            r = self.session.post(
                f"{self.base_url}/passwords/{password_id}/trash",
                timeout=self.timeout,
            )
            if r.ok:
                return True, "ok"
            return False, f"{r.status_code}: {r.text}"
        except Exception as e:
            return False, str(e)

    def restore_password(self, password_id: int) -> Tuple[bool, str]:
        try:
            r = self.session.post(
                f"{self.base_url}/passwords/{password_id}/restore",
                timeout=self.timeout,
            )
            if r.ok:
                return True, "ok"
            return False, f"{r.status_code}: {r.text}"
        except Exception as e:
            return False, str(e)

    def delete_password(self, password_id: int) -> Tuple[bool, str]:
        try:
            r = self.session.delete(
                f"{self.base_url}/passwords/{password_id}",
                timeout=self.timeout,
            )
            if r.ok:
                return True, "ok"
            return False, f"{r.status_code}: {r.text}"
        except Exception as e:
            return False, str(e)

    def reveal_password(self, password_id: int) -> Tuple[bool, str, str]:
        """
        ✅ FIXED: Use GET request instead of POST
        Get decrypted password from backend
        Returns: (success, message, plain_password)
        """
        try:
            print(f"\n🔓 Revealing password ID={password_id}")
            
            r = self.session.get(
                f"{self.base_url}/passwords/{password_id}/reveal",
                timeout=self.timeout,
            )
            
            print(f"📥 Reveal response: Status={r.status_code}")
            
            if r.ok:
                data = r.json()
                password = data.get("password", "")
                print(f"✅ Password revealed successfully (length: {len(password)})")
                return True, "ok", password
            else:
                error_msg = r.text
                try:
                    error_json = r.json()
                    error_msg = error_json.get('error', r.text)
                except:
                    pass
                print(f"❌ Reveal failed: {error_msg}")
                return False, f"{r.status_code}: {error_msg}", ""
                
        except Exception as e:
            print(f"❌ Exception in reveal_password: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e), ""

    def verify_password(self, password_id: int, plain_password: str) -> Tuple[bool, str, str]:
        """
        Verify a password against its hash (for 2FA operations)
        Returns: (success, message, plain_password if valid)
        """
        try:
            r = self.session.post(
                f"{self.base_url}/passwords/{password_id}/verify",
                json={"password": plain_password},
                timeout=self.timeout,
            )
            if r.ok:
                data = r.json()
                if data.get("valid"):
                    return True, "ok", data.get("password", "")
                else:
                    return False, "Invalid password", ""
            return False, f"{r.status_code}: {r.text}", ""
        except Exception as e:
            return False, str(e), ""

    def toggle_favorite(self, password_id: int) -> Tuple[bool, str, bool]:
        """
        Toggle favorite status for a password
        Returns: (success, message, new_favorite_status)
        """
        try:
            r = self.session.patch(
                f"{self.base_url}/passwords/{password_id}/favorite",
                timeout=self.timeout,
            )
            if r.ok:
                data = r.json()
                return True, "ok", data.get("favorite", False)
            return False, f"{r.status_code}: {r.text}", False
        except Exception as e:
            return False, str(e), False