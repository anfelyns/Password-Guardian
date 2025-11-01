"""
Check what's actually stored in the database for tiribrk.com
Run from project root: python check_password.py
"""

import sys
import os
import mysql.connector

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from backend.encryption import EncryptionManager

def check_password():
    print("="*60)
    print("🔍 Checking Password in Database")
    print("="*60)
    
    # Connect to database
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='inessouai2005_',
            database='password_guardian',
            port=3306
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # Get tiribrk.com password
        cursor.execute("""
            SELECT id, site_name, username, encrypted_password, category, strength
            FROM passwords 
            WHERE site_name LIKE '%tiribrk%' OR site_name LIKE '%tiribr%'
            ORDER BY id DESC
            LIMIT 1
        """)
        
        password = cursor.fetchone()
        
        if not password:
            print("❌ No password found for tiribrk.com")
            return
        
        print(f"\n📋 Password Info:")
        print(f"  ID: {password['id']}")
        print(f"  Site: {password['site_name']}")
        print(f"  Username: {password['username']}")
        print(f"  Category: {password['category']}")
        print(f"  Strength: {password['strength']}")
        
        encrypted = password['encrypted_password']
        print(f"\n🔐 Encrypted password (stored in DB):")
        print(f"  Length: {len(encrypted)} characters")
        print(f"  First 80 chars: {encrypted[:80]}")
        print(f"  Last 20 chars: ...{encrypted[-20:]}")
        
        # Try to decrypt
        print(f"\n🔓 Attempting to decrypt...")
        em = EncryptionManager()
        
        try:
            decrypted = em.decrypt(encrypted)
            print(f"✅ Decryption successful!")
            print(f"🔓 Decrypted password: {decrypted}")
            print(f"  Length: {len(decrypted)} characters")
            
            # Check if it looks like it was encrypted twice
            if len(decrypted) > 50 and '=' in decrypted:
                print(f"\n⚠️ WARNING: This looks like it might have been encrypted TWICE!")
                print(f"  Trying to decrypt again...")
                
                try:
                    double_decrypted = em.decrypt(decrypted)
                    print(f"✅ Double decryption successful!")
                    print(f"🔓 Actual password: {double_decrypted}")
                except Exception as e:
                    print(f"❌ Double decryption failed: {e}")
            
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            import traceback
            traceback.print_exc()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_password()
