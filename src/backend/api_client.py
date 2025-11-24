# src/backend/api_client.py
import requests
from typing import Tuple, List, Dict, Any

from src.security.encryption import decrypt_any



class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:5001", timeout: int = 15):
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
        encrypted_password: str,
        category: str,
        site_url: str = "",
    ) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            payload = {
                "user_id": user_id,
                "site_name": site_name,
                "site_url": site_url,
                "username": username,
                "encrypted_password": encrypted_password,
                "category": category,
            }
            r = self.session.post(
                f"{self.base_url}/passwords",
                json=payload,
                timeout=self.timeout,
            )
            if r.ok:
                return True, "ok", r.json()
            return False, f"{r.status_code}: {r.text}", {}
        except Exception as e:
            return False, str(e), {}

    def update_password(self, password_id: int, updates: Dict[str, Any]) -> Tuple[bool, str]:
        try:
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
        """Ask backend for the encrypted blob; UI will decrypt locally."""
        try:
            r = self.session.get(
                f"{self.base_url}/passwords/{password_id}/reveal",
                timeout=self.timeout,
            )
            if r.ok:
                enc = r.json().get("encrypted_password", "")
                return True, "ok", enc
            return False, f"{r.status_code}: {r.text}", ""
        except Exception as e:
            return False, str(e), ""

    # ---------- LOCAL DECRYPT HELP ----------
    def decrypt_password(self, encrypted_blob: str) -> str:
        """Decrypts the storage blob using your AES-GCM helper."""
        return decrypt_any(encrypted_blob)
