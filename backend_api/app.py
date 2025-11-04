"""
backend_api/app.py - Complete Backend API with 48h Trash Auto-Cleanup
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime, timedelta
import random
import string
import threading
import time

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'inessouai2005_',
    'database': 'password_guardian',
    'port': 3306
}

def get_db_connection():
    """Get MySQL database connection"""
    return mysql.connector.connect(**DB_CONFIG)


@app.route('/', methods=['GET'])
def index():
    """API health check"""
    return jsonify({
        'status': 'online',
        'message': 'SecureVault Backend API',
        'version': '1.0.0',
        'features': {
            'trash_cleanup': '48h auto-delete',
            'encryption': 'Client-side AES-256'
        }
    })


@app.route('/passwords/suggestion', methods=['GET'])
def get_password_suggestion():
    """Generate strong password suggestion"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    length = int(request.args.get('length', 16))
    password = ''.join(random.choice(chars) for _ in range(length))
    return jsonify({'suggestion': password})


@app.route('/passwords', methods=['POST'])
def add_password():
    """Add new password"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        site_name = data.get('site_name')
        username = data.get('username')
        encrypted_password = data.get('encrypted_password')
        category = data.get('category', 'personal')
        favorite = data.get('favorite', False)
        
        if not all([user_id, site_name, username, encrypted_password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Determine strength based on encrypted password length
        if len(encrypted_password) > 100:
            strength = 'strong'
        elif len(encrypted_password) > 60:
            strength = 'medium'
        else:
            strength = 'weak'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO passwords 
            (user_id, site_name, username, encrypted_password, category, strength, favorite, created_at, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        
        cursor.execute(query, (
            user_id, site_name, username, encrypted_password, 
            category, strength, favorite
        ))
        
        conn.commit()
        password_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        print(f"✅ Password added: ID={password_id}, Site={site_name}, User={user_id}, Category={category}")
        
        return jsonify({
            'message': 'Password added successfully',
            'id': password_id
        }), 201
        
    except Exception as e:
        print(f"❌ Error adding password: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/passwords/<int:user_id>', methods=['GET'])
def get_passwords(user_id):
    """Get all passwords for a user (including trash)"""
    try:
        print(f"\n🔍 GET /passwords/{user_id} - Fetching passwords...")
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT id, user_id, site_name, site_icon, username, 
                   encrypted_password, category, strength, favorite, 
                   last_updated, created_at
            FROM passwords 
            WHERE user_id = %s
            ORDER BY 
                CASE WHEN category = 'trash' THEN 1 ELSE 0 END,
                created_at DESC
        """
        
        cursor.execute(query, (user_id,))
        passwords = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Format dates
        for pwd in passwords:
            if pwd.get('last_updated'):
                pwd['last_updated'] = pwd['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
            if pwd.get('created_at'):
                pwd['created_at'] = pwd['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            pwd['favorite'] = bool(pwd.get('favorite', False))
        
        print(f"✅ Retrieved {len(passwords)} passwords for user {user_id}")
        
        return jsonify(passwords), 200
        
    except Exception as e:
        print(f"❌ Error getting passwords: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/passwords/<int:password_id>', methods=['PUT'])
def update_password(password_id):
    """Update existing password (including move to/from trash)"""
    try:
        data = request.get_json()
        
        site_name = data.get('site_name')
        username = data.get('username')
        encrypted_password = data.get('encrypted_password')
        category = data.get('category')
        favorite = data.get('favorite', False)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            UPDATE passwords 
            SET site_name = %s, username = %s, encrypted_password = %s, 
                category = %s, favorite = %s, last_updated = NOW()
            WHERE id = %s
        """
        
        cursor.execute(query, (
            site_name, username, encrypted_password, 
            category, favorite, password_id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        action = "moved to trash" if category == "trash" else f"updated (category: {category})"
        print(f"✅ Password {action}: ID={password_id}")
        
        return jsonify({'message': 'Password updated successfully'}), 200
        
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/passwords/<int:password_id>', methods=['DELETE'])
def delete_password(password_id):
    """Permanent delete password"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get password info before deleting
        cursor.execute("SELECT site_name, category FROM passwords WHERE id = %s", (password_id,))
        pwd_info = cursor.fetchone()
        
        query = "DELETE FROM passwords WHERE id = %s"
        cursor.execute(query, (password_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        site = pwd_info[0] if pwd_info else "Unknown"
        print(f"🗑️ Password PERMANENTLY deleted: ID={password_id}, Site={site}")
        
        return jsonify({'message': 'Password deleted permanently'}), 200
        
    except Exception as e:
        print(f"❌ Error deleting password: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/passwords/<int:password_id>/reveal', methods=['GET'])
def reveal_password(password_id):
    """Get encrypted password for decryption"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT encrypted_password FROM passwords WHERE id = %s"
        cursor.execute(query, (password_id,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Password not found'}), 404
        
        return jsonify({'encrypted_password': result['encrypted_password']}), 200
        
    except Exception as e:
        print(f"❌ Error revealing password: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/passwords/favorites/<int:user_id>', methods=['GET'])
def get_favorites(user_id):
    """Get favorite passwords"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT * FROM passwords 
            WHERE user_id = %s AND favorite = TRUE AND category != 'trash'
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (user_id,))
        passwords = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(passwords), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/passwords/category/<int:user_id>/<string:category>', methods=['GET'])
def get_by_category(user_id, category):
    """Get passwords by category"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT * FROM passwords 
            WHERE user_id = %s AND category = %s
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (user_id, category))
        passwords = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(passwords), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/passwords/trash/cleanup', methods=['POST'])
def manual_cleanup():
    """Manual trash cleanup (for testing)"""
    try:
        deleted = cleanup_old_trash()
        return jsonify({
            'message': 'Cleanup completed',
            'deleted_count': deleted
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def cleanup_old_trash():
    """Clean up passwords in trash older than 48 hours"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate 48 hours ago
        cutoff_time = datetime.now() - timedelta(hours=48)
        
        # Find passwords to delete
        cursor.execute("""
            SELECT id, site_name, last_updated 
            FROM passwords 
            WHERE category = 'trash' AND last_updated < %s
        """, (cutoff_time,))
        
        to_delete = cursor.fetchall()
        
        if to_delete:
            # Delete old trash items
            query = """
                DELETE FROM passwords 
                WHERE category = 'trash' AND last_updated < %s
            """
            cursor.execute(query, (cutoff_time,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"🗑️ Auto-cleanup: Deleted {deleted_count} passwords from trash (>48h old)")
            for pwd_id, site_name, last_updated in to_delete:
                hours_old = (datetime.now() - last_updated).total_seconds() / 3600
                print(f"   └─ ID={pwd_id}, Site={site_name}, Age={hours_old:.1f}h")
        else:
            deleted_count = 0
        
        cursor.close()
        conn.close()
        
        return deleted_count
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return 0


def trash_cleanup_worker():
    """Background worker that runs cleanup every hour"""
    print("🔄 Trash cleanup worker started (checks every hour)")
    
    while True:
        try:
            # Wait 1 hour
            time.sleep(3600)
            
            # Run cleanup
            deleted = cleanup_old_trash()
            
            if deleted == 0:
                print("✓ Trash cleanup check: No items to delete")
            
        except Exception as e:
            print(f"❌ Trash cleanup worker error: {e}")


# Start background cleanup thread
cleanup_thread = threading.Thread(target=trash_cleanup_worker, daemon=True, name="TrashCleanup")
cleanup_thread.start()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔒 SecureVault Backend API")
    print("="*60)
    print(f"🌐 Server: http://localhost:5000")
    print(f"🔐 Encryption: Client-side AES-256")
    print(f"💾 Database: MySQL (password_guardian)")
    print(f"🗑️ Trash auto-cleanup: 48 hours")
    print(f"⏰ Cleanup check: Every 1 hour")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)