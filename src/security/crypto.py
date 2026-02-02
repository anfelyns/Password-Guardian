# -*- coding: utf-8 -*-
"""Client-side style vault crypto helpers.

Uni-project "pro" upgrade goals:
- Per-user vault key derived from the *master password* using Argon2id.
- Authenticated encryption using AES-256-GCM.

This module is intentionally small and easy to explain in a report.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class KdfParams:
    time_cost: int = 3
    memory_cost_kib: int = 65536  # 64 MiB
    parallelism: int = 2
    hash_len: int = 32  # 256-bit key


def new_salt() -> str:
    """Return a URL-safe base64 salt string."""
    return base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8").rstrip("=")


def derive_vault_key(master_password: str, salt_b64: str, params: KdfParams | None = None) -> bytes:
    """Derive a 256-bit vault key from a master password + salt using Argon2id."""
    if params is None:
        params = KdfParams()
    salt = base64.urlsafe_b64decode(_pad_b64(salt_b64))
    return hash_secret_raw(
        secret=master_password.encode("utf-8"),
        salt=salt,
        time_cost=params.time_cost,
        memory_cost=params.memory_cost_kib,
        parallelism=params.parallelism,
        hash_len=params.hash_len,
        type=Type.ID,
    )


def encrypt_secret(plain: str, key: bytes) -> str:
    """Encrypt a secret and return a compact base64 payload."""
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plain.encode("utf-8"), associated_data=None)
    payload = nonce + ct
    return base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")


def decrypt_secret(payload_b64: str, key: bytes) -> str:
    """Decrypt a base64 payload produced by encrypt_secret."""
    if not payload_b64:
        return ""
    # Support optional prefix (zk1:)
    if payload_b64.startswith("zk1:"):
        payload_b64 = payload_b64.split("zk1:", 1)[1]
    raw = base64.urlsafe_b64decode(_pad_b64(payload_b64))
    nonce, ct = raw[:12], raw[12:]
    aes = AESGCM(key)
    pt = aes.decrypt(nonce, ct, associated_data=None)
    return pt.decode("utf-8")


def _pad_b64(s: str) -> str:
    return s + "=" * (-len(s) % 4)
