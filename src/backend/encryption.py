# src/backend/encryption.py
"""
Client-side AES-256 encryption for passwords
"""
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import base64


class EncryptionManager:
    """Handles AES-256 encryption/decryption for passwords"""
    
    def __init__(self, master_key: str = None):
        """
        Initialize encryption with a master key.
        
        Args:
            master_key: Master password for encryption. 
                       If None, uses default (NOT SECURE - for demo only)
        """
        if master_key is None:
            # Default key for demo - IN PRODUCTION, use user's actual master password
            master_key = "SecureVault2025MasterKey!@#"
        
        # Derive a 256-bit key from master key using PBKDF2
        self.key = PBKDF2(
            master_key.encode('utf-8'),
            b'securevault_salt_2025',  # In production: unique per user
            dkLen=32,  # 256 bits for AES-256
            count=100000
        )
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext password using AES-256-CBC
        
        Args:
            plaintext: Password to encrypt
            
        Returns:
            Base64 encoded string: IV + encrypted_data
        """
        if not plaintext:
            return ""
        
        try:
            # Generate random IV (16 bytes for AES)
            iv = get_random_bytes(16)
            
            # Create AES cipher in CBC mode
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            
            # Pad plaintext to multiple of 16 bytes
            padded_data = self._pad(plaintext.encode('utf-8'))
            
            # Encrypt
            encrypted_data = cipher.encrypt(padded_data)
            
            # Combine IV + encrypted data and encode to base64
            result = base64.b64encode(iv + encrypted_data).decode('utf-8')
            
            return result
            
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt encrypted password
        
        Args:
            encrypted: Base64 encoded encrypted password (IV + data)
            
        Returns:
            Decrypted plaintext password
        """
        if not encrypted:
            return ""
        
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted.encode('utf-8'))
            
            # Extract IV (first 16 bytes) and ciphertext
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # Create AES cipher
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            
            # Decrypt
            decrypted_padded = cipher.decrypt(ciphertext)
            
            # Remove padding
            decrypted = self._unpad(decrypted_padded).decode('utf-8')
            
            return decrypted
            
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            # Return encrypted text if decryption fails (for debugging)
            return f"[DECRYPT_ERROR: {str(e)[:50]}]"
    
    def _pad(self, data: bytes) -> bytes:
        """
        Pad data to multiple of 16 bytes using PKCS7 padding
        
        Args:
            data: Data to pad
            
        Returns:
            Padded data
        """
        padding_length = 16 - (len(data) % 16)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _unpad(self, data: bytes) -> bytes:
        """
        Remove PKCS7 padding
        
        Args:
            data: Padded data
            
        Returns:
            Unpadded data
        """
        padding_length = data[-1]
        return data[:-padding_length]


# Test the encryption
if __name__ == "__main__":
    print("Testing EncryptionManager...")
    
    em = EncryptionManager()
    
    # Test cases
    test_passwords = [
        "SimplePassword123",
        "Complex!@#$%^&*()_+Password",
        "émojis🔐🛡️test",
        "a" * 100  # Long password
    ]
    
    for pwd in test_passwords:
        print(f"\n📝 Original: {pwd[:50]}{'...' if len(pwd) > 50 else ''}")
        
        encrypted = em.encrypt(pwd)
        print(f"🔒 Encrypted: {encrypted[:80]}...")
        
        decrypted = em.decrypt(encrypted)
        print(f"🔓 Decrypted: {decrypted[:50]}{'...' if len(decrypted) > 50 else ''}")
        
        if pwd == decrypted:
            print("✅ PASS - Encryption/Decryption successful")
        else:
            print("❌ FAIL - Mismatch!")
    
    print("\n" + "="*60)
    print("Encryption tests completed!")