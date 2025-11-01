"""
Script to create a test user in the database
Run this before launching the application for the first time
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.auth.auth_manager import AuthManager


def create_test_user():
    """Create a test user for development"""
    print("=" * 50)
    print("Password Guardian - Create Test User")
    print("=" * 50)
    
    auth = AuthManager()
    
    print("\nEnter new user details:")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    confirm = input("Confirm Password: ").strip()
    
    if not username or not email or not password:
        print("\n❌ All fields are required!")
        return
    
    if password != confirm:
        print("\n❌ Passwords don't match!")
        return
    
    if len(password) < 8:
        print("\n❌ Password must be at least 8 characters!")
        return
    
    print("\nCreating user...")
    success, message = auth.register_user(username, email, password)
    
    if success:
        print(f"\n✅ {message}")
        print(f"\nYou can now login with:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
    else:
        print(f"\n❌ {message}")


def test_login():
    """Test login with credentials"""
    print("\n" + "=" * 50)
    print("Test Login")
    print("=" * 50)
    
    auth = AuthManager()
    
    username = input("\nUsername or Email: ").strip()
    password = input("Password: ").strip()
    
    print("\nAuthenticating...")
    success, user_data, message = auth.authenticate(username, password)
    
    if success:
        print(f"\n✅ {message}")
        print(f"\nUser Data:")
        print(f"  ID: {user_data['id']}")
        print(f"  Username: {user_data['username']}")
        print(f"  Email: {user_data['email']}")
    else:
        print(f"\n❌ {message}")


if __name__ == "__main__":
    while True:
        print("\n" + "=" * 50)
        print("Password Guardian - User Management")
        print("=" * 50)
        print("\n1. Create new user")
        print("2. Test login")
        print("3. Exit")
        
        choice = input("\nChoose an option (1-3): ").strip()
        
        if choice == "1":
            create_test_user()
        elif choice == "2":
            test_login()
        elif choice == "3":
            print("\nGoodbye!")
            break
        else:
            print("\n❌ Invalid choice!")