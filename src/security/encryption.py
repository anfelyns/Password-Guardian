# src/security/encryption.py
# AES-GCM Encryption / Decryption Utilities for Password Guardian

import os
import base64
import hashlib
from typing import Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ================================================================
#  MASTER KEY HANDLING
# ================================================================
def _get_master_key() -> bytes:
    """
    Derive a stable 32-byte AES key.
    You can override it by setting the environment variable PWG_MASTER.

    Example (PowerShell):
        $env:PWG_MASTER = "my-ultra-secret-key"
    """
    secret = os.environ.get("PWG_MASTER", "dev-master-password-guardian")
    return hashlib.blake2b(secret.encode("utf-8"), digest_size=32).digest()


# ================================================================
#  ENCRYPTION
# ================================================================
def encrypt_for_storage(plain: Union[str, bytes]) -> str:
    """
    Encrypt plaintext using AES-GCM and return a compact token:
        gcm1:<base64(nonce|ciphertext|tag)>
    """
    if isinstance(plain, str):
        plain = plain.encode("utf-8")

    key = _get_master_key()
    aes = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce

    ct = aes.encrypt(nonce, plain, associated_data=None)
    blob = nonce + ct
    token = "gcm1:" + base64.b64encode(blob).decode("ascii")
    return token


# ================================================================
#  DECRYPTION
# ================================================================
def decrypt_any(token: Union[str, bytes]) -> str:
    """
    Decrypt data previously encrypted with encrypt_for_storage().
    Raises ValueError with friendly messages if format or key is wrong.
    """
    if isinstance(token, bytes):
        token = token.decode("utf-8", errors="ignore")

    if not token:
        raise ValueError("Empty token")

    # ---- GCM format ---------------------------------------------------------
    if token.startswith("gcm1:"):
        b64 = token.split("gcm1:", 1)[1]
        try:
            blob = base64.b64decode(b64)
        except Exception as e:
            raise ValueError(f"Invalid base64 payload: {e}")

        if len(blob) < 28:
            raise ValueError("Invalid GCM blob length")

        nonce = blob[:12]
        ct_tag = blob[12:]

        key = _get_master_key()
        aes = AESGCM(key)

        try:
            pt = aes.decrypt(nonce, ct_tag, associated_data=None)
        except Exception as e:
            msg = str(e)
            if "Authentication" in msg or "tag" in msg or "MAC" in msg:
                raise ValueError("MAC check failed")
            raise ValueError(msg)
        return pt.decode("utf-8")

    # ---- Unknown format -----------------------------------------------------
    raise ValueError("Unknown encryption format")
