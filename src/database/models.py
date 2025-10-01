from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    salt: str
    created_at: datetime
    last_login: Optional[datetime]

@dataclass
class PasswordEntry:
    id: int
    user_id: int
    site_name: str
    site_icon: str
    username: str
    encrypted_password: str
    category: str
    strength: str
    favorite: bool
    last_updated: datetime
    created_at: datetime
    
