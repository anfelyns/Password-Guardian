# -*- coding: utf-8 -*-
"""
Database Migration Script
Migrates from old schema to new enhanced schema
"""
import mysql.connector
import sys
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'inessouai2005_',
    'database': 'password_guardian',
    'port': 3306
}

def get_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def backup_database():
    """Create backup of existing data"""
    print("\n📦 Creating backup...")
    
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    
    backup_data = {
        'users': [],
        'passwords': [],
        'sessions': [],
        'activity_logs': [],
        'otp_codes': [],
        'suspicious_logins': []
    }
    
    try:
        # Backup each table
        for table in backup_data.keys():
            try:
                cursor.execute(f"SELECT * FROM {table}")
                backup_data[table] = cursor.fetchall()
                print(f"  ✅ Backed up {table}: {len(backup_data[table])} rows")
            except Exception as e:
                print(f"  ⚠️  Table {table} not found or empty: {e}")
        
        # Save to file
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(backup_file, 'w') as f:
            f.write(f"Backup created: {datetime.now()}\n")
            f.write(f"Database: {DB_CONFIG['database']}\n\n")
            for table, data in backup_data.items():
                f.write(f"\n{'='*50}\n")
                f.write(f"Table: {table} ({len(data)} rows)\n")
                f.write(f"{'='*50}\n")
                for row in data:
                    f.write(f"{row}\n")
        
        print(f"\n✅ Backup saved to: {backup_file}")
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def check_existing_schema():
    """Check what tables currently exist"""
    print("\n🔍 Checking existing schema...")
    
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"  Found {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"    • {table}: {count} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def add_missing_columns():
    """Add new columns to existing tables"""
    print("\n🔧 Adding missing columns...")
    
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    migrations = [
        # Users table updates
        ("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE", "email_verified to users"),
        ("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE", "is_verified to users"),
        ("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code VARCHAR(10)", "verification_code to users"),
        ("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_expires_at TIMESTAMP NULL", "verification_expires_at to users"),
        ("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_device VARCHAR(255)", "last_device to users"),
        
        # Activity logs updates
        ("ALTER TABLE activity_logs ADD COLUMN IF NOT EXISTS target_type VARCHAR(50)", "target_type to activity_logs"),
        ("ALTER TABLE activity_logs ADD COLUMN IF NOT EXISTS target_id INT", "target_id to activity_logs"),
        ("ALTER TABLE activity_logs ADD COLUMN IF NOT EXISTS device_info VARCHAR(255)", "device_info to activity_logs"),
        ("ALTER TABLE activity_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)", "ip_address to activity_logs"),
        
        # Sessions updates
        ("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS session_token VARCHAR(255)", "session_token to sessions"),
        ("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", "last_activity to sessions"),
        ("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE", "is_active to sessions"),
        
        # OTP codes updates
        ("ALTER TABLE otp_codes ADD COLUMN IF NOT EXISTS purpose VARCHAR(50) DEFAULT 'login'", "purpose to otp_codes"),
    ]
    
    success_count = 0
    for sql, description in migrations:
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"  ✅ Added {description}")
            success_count += 1
        except Exception as e:
            if "Duplicate column" in str(e):
                print(f"  ℹ️  Column already exists: {description}")
                success_count += 1
            else:
                print(f"  ⚠️  Failed to add {description}: {e}")
    
    cursor.close()
    conn.close()
    
    print(f"\n✅ Migration completed: {success_count}/{len(migrations)} columns")
    return True

def create_new_tables():
    """Create new tables if they don't exist"""
    print("\n🆕 Creating new tables...")
    
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    new_tables = [
        # User devices table
        ("""
        CREATE TABLE IF NOT EXISTS user_devices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            fingerprint VARCHAR(255) NOT NULL,
            label VARCHAR(255),
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_fingerprint (fingerprint),
            UNIQUE KEY unique_device (user_id, fingerprint)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """, "user_devices"),
        
        # Password history table
        ("""
        CREATE TABLE IF NOT EXISTS password_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            password_id INT NOT NULL,
            old_encrypted_password TEXT NOT NULL,
            old_strength ENUM('weak', 'medium', 'strong') NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (password_id) REFERENCES passwords(id) ON DELETE CASCADE,
            INDEX idx_password_id (password_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """, "password_history"),
    ]
    
    for sql, table_name in new_tables:
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"  ✅ Created table: {table_name}")
        except Exception as e:
            print(f"  ℹ️  Table {table_name} already exists or error: {e}")
    
    cursor.close()
    conn.close()
    
    return True

def add_indexes():
    """Add performance indexes"""
    print("\n📈 Adding performance indexes...")
    
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    indexes = [
        ("CREATE INDEX IF NOT EXISTS idx_email ON users(email)", "idx_email"),
        ("CREATE INDEX IF NOT EXISTS idx_username ON users(username)", "idx_username"),
        ("CREATE INDEX IF NOT EXISTS idx_verified ON users(email_verified)", "idx_verified"),
        ("CREATE INDEX IF NOT EXISTS idx_user_category ON passwords(user_id, category)", "idx_user_category"),
        ("CREATE INDEX IF NOT EXISTS idx_user_favorite ON passwords(user_id, favorite)", "idx_user_favorite"),
        ("CREATE INDEX IF NOT EXISTS idx_user_timestamp ON activity_logs(user_id, timestamp)", "idx_user_timestamp"),
    ]
    
    for sql, index_name in indexes:
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"  ✅ Added index: {index_name}")
        except Exception as e:
            if "Duplicate key" in str(e) or "already exists" in str(e):
                print(f"  ℹ️  Index already exists: {index_name}")
            else:
                print(f"  ⚠️  Failed to add index {index_name}: {e}")
    
    cursor.close()
    conn.close()
    
    return True

def verify_migration():
    """Verify migration was successful"""
    print("\n✅ Verifying migration...")
    
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Check critical columns exist
        critical_checks = [
            ("SELECT email_verified FROM users LIMIT 1", "users.email_verified"),
            ("SELECT verification_code FROM users LIMIT 1", "users.verification_code"),
            ("SELECT session_token FROM sessions LIMIT 1", "sessions.session_token"),
            ("SELECT purpose FROM otp_codes LIMIT 1", "otp_codes.purpose"),
        ]
        
        all_good = True
        for sql, check_name in critical_checks:
            try:
                cursor.execute(sql)
                print(f"  ✅ Verified: {check_name}")
            except Exception as e:
                print(f"  ❌ Missing: {check_name}")
                all_good = False
        
        if all_good:
            print("\n🎉 Migration completed successfully!")
        else:
            print("\n⚠️  Some checks failed. Review the output above.")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main migration process"""
    print("="*60)
    print("🔄 Password Guardian - Database Migration")
    print("="*60)
    
    # Step 1: Check connection
    print("\n1️⃣ Testing database connection...")
    conn = get_connection()
    if not conn:
        print("❌ Cannot connect to database. Check your credentials in DB_CONFIG.")
        sys.exit(1)
    conn.close()
    print("✅ Database connection successful")
    
    # Step 2: Check existing schema
    if not check_existing_schema():
        print("❌ Schema check failed")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Step 3: Backup
    print("\n2️⃣ Creating backup...")
    response = input("Create backup before migration? (recommended) (y/n): ")
    if response.lower() == 'y':
        if not backup_database():
            print("⚠️  Backup failed, but continuing...")
    
    # Step 4: Add missing columns
    print("\n3️⃣ Adding missing columns...")
    if not add_missing_columns():
        print("⚠️  Some columns may not have been added")
    
    # Step 5: Create new tables
    print("\n4️⃣ Creating new tables...")
    if not create_new_tables():
        print("⚠️  Some tables may not have been created")
    
    # Step 6: Add indexes
    print("\n5️⃣ Adding performance indexes...")
    if not add_indexes():
        print("⚠️  Some indexes may not have been added")
    
    # Step 7: Verify
    print("\n6️⃣ Verifying migration...")
    verify_migration()
    
    print("\n" + "="*60)
    print("📝 Next Steps:")
    print("="*60)
    print("1. Review the backup file created")
    print("2. Test user registration with email verification")
    print("3. Test login functionality")
    print("4. Update your .env file with email credentials")
    print("5. Run: python main.py")
    print("\n💡 For complete schema, run:")
    print("   mysql -u root -p < database/schema_merged.sql")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed with error: {e}")
        sys.exit(1)