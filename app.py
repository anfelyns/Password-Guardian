
from flask import Flask, request, jsonify
from db import get_db_connection
import random, string
from Crypto.Cipher import AES
import base64
import os  # For generating random bytes


app = Flask(__name__)

# ================== AES ENCRYPTION ==================

SECRET_KEY = b"1234567890123456"  # AES secret key (must be 16/24/32 bytes)

def encrypt_password(password: str) -> str:
    """Encrypt a password using AES (CBC mode) with random IV."""
    # Generate a NEW random IV each time
    IV = os.urandom(16)  # 16 random bytes
    
    # Create AES cipher in CBC mode with the IV
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    
    # Add padding to make password length multiple of 16
    padding_length = 16 - (len(password) % 16)
    password_padded = password + chr(padding_length) * padding_length
    
    # Encrypt the padded password
    encrypted = cipher.encrypt(password_padded.encode('utf-8'))
    
    # Combine IV and encrypted data for storage
    combined = IV + encrypted  # IV (16 bytes) + encrypted data
    return base64.b64encode(combined).decode('utf-8')

def decrypt_password(encrypted_password: str) -> str:
    """Decrypt an AES encrypted password."""
    # Decode from base64
    combined_bytes = base64.b64decode(encrypted_password)
    
    # Extract IV (first 16 bytes) and encrypted data
    IV = combined_bytes[:16]  # First 16 bytes = IV
    encrypted_data = combined_bytes[16:]  # Remaining bytes = encrypted data
    
    # Create AES cipher with the extracted IV
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    
    # Decrypt and decode to string
    decrypted = cipher.decrypt(encrypted_data).decode('utf-8')
    
    # Remove padding based on the last character
    padding_length = ord(decrypted[-1])
    return decrypted[:-padding_length]


# ================== HELPERS ==================

def check_password_strength(password: str) -> str:
    """Check password strength (weak, medium, strong)."""
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in string.punctuation for c in password)

    if length >= 12 and has_upper and has_digit and has_symbol:
        return "strong"
    elif length >= 8 and (has_digit or has_symbol):
        return "medium"
    else:
        return "weak"

def generate_strong_password(length=12):
    """Generate a password that is ALWAYS strong"""
    
    # Verification de la longueur minimale
    if length < 12:
        length = 12  # Force minimum 12 caracteres
    
    # Caracteres par categorie
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = string.punctuation
    
    # Garantir au moins 1 caractere de chaque type
    password = [
        random.choice(uppercase),  # Au moins 1 majuscule
        random.choice(digits),     # Au moins 1 chiffre
        random.choice(symbols),    # Au moins 1 symbole
    ]
    
    # Remplir le reste avec tous les caracteres melangs
    all_chars = lowercase + uppercase + digits + symbols
    for _ in range(length - 3):  # -3 car on a deja 3 caracteres
        password.append(random.choice(all_chars))
    
    # Melanger pour eviter un motif previsible
    random.shuffle(password)
    
    return ''.join(password)
    # ================== API ROUTES ==================

#  Add a new password
@app.route("/passwords", methods=["POST"])
def add_password():
    try:
        data = request.json
        
        # Check required fields
        required_fields = ['user_id', 'site_name', 'username', 'password', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Field {field} is required"}), 400
        
        # Validate category
        valid_categories = ['personal', 'work', 'finance', 'study', 'game']
        if data['category'] not in valid_categories:
            return jsonify({"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}), 400
        
        # Calculate strength of the original password
        strength = check_password_strength(data['password'])

        # Encrypt password before storage
        encrypted = encrypt_password(data['password'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO passwords 
               (user_id, site_name, username, encrypted_password, category, strength, favorite) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (data['user_id'], data['site_name'], data['username'], 
             encrypted, data['category'], strength, data.get('favorite', False))
        )
        conn.commit()
        cursor.close()
        conn.close()

        if strength in ["weak", "medium"]:
            suggestion = generate_strong_password(14)
            return jsonify({
                "message": "Password added  but it is weak or medium ",
                "strength": strength,
                "suggestion": suggestion
            })
        else:
            return jsonify({"message": "Password added ", "strength": strength})
    
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


#  List all passwords for a user
@app.route("/passwords/<int:user_id>", methods=["GET"])
def get_passwords(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM passwords WHERE user_id=%s ORDER BY last_updated DESC", (user_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        # Hide real password in the response
        for r in results:
            r['password_display'] = "*******"
            if 'encrypted_password' in r:
                del r['encrypted_password']

        return jsonify(results)
    
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# Reveal a specific password
@app.route("/passwords/<int:pwd_id>/reveal", methods=["GET"])
def reveal_password(pwd_id):
    """Reveal the actual password only when requested."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT encrypted_password FROM passwords WHERE id=%s", (pwd_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return jsonify({"error": "Password not found"}), 404

        # Decrypt only on request
        real_password = decrypt_password(result['encrypted_password'])
        
        return jsonify({
            "real_password": real_password,
            "message": "Password revealed - use with caution!"
        })
    
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# Update a password
@app.route("/passwords/<int:pwd_id>", methods=["PUT"])
def update_password(pwd_id):
    try:
        data = request.json
        
        # Check required fields
        required_fields = ['site_name', 'username', 'password', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Field {field} is required"}), 400
        
        # Validate category
        valid_categories = ['personal', 'work', 'finance', 'study', 'game']
        if data['category'] not in valid_categories:
            return jsonify({"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}), 400
        
        # Calculate strength
        strength = check_password_strength(data['password'])

        # Encrypt new password
        encrypted = encrypt_password(data['password'])

        conn = get_db_connection()
        cursor = conn.cursor()
        # Removed last_updated=NOW(), DB will auto-update timestamp
        cursor.execute(
            """UPDATE passwords 
               SET site_name=%s, username=%s, encrypted_password=%s, category=%s, 
                   strength=%s, favorite=%s
               WHERE id=%s""",
            (data['site_name'], data['username'], encrypted, 
             data['category'], strength, data.get('favorite', False), pwd_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        if strength in ["weak", "medium"]:
            suggestion = generate_strong_password(14)
            return jsonify({
                "message": "Password updated  but it is weak or medium ",
                "strength": strength,
                "suggestion": suggestion
            })
        else:
            return jsonify({"message": "Password updated ", "strength": strength})
    
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


#  Delete a password
@app.route("/passwords/<int:pwd_id>", methods=["DELETE"])
def delete_password(pwd_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM passwords WHERE id=%s", (pwd_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Password deleted "})
    
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


#  Get favorite passwords
@app.route("/passwords/favorites/<int:user_id>", methods=["GET"])
def get_favorites(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM passwords WHERE user_id=%s AND favorite=1 ORDER BY last_updated DESC", (user_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        for r in results:
            r['password_display'] = "*******"
            if 'encrypted_password' in r:
                del r['encrypted_password']

        return jsonify(results)
    
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


#  Filter by category
@app.route("/passwords/category/<int:user_id>/<string:cat>", methods=["GET"])
def get_by_category(user_id, cat):
    try:
        valid_categories = ['personal', 'work', 'finance', 'study', 'game']
        if cat not in valid_categories:
            return jsonify({"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM passwords WHERE user_id=%s AND category=%s ORDER BY last_updated DESC", (user_id, cat))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        for r in results:
            r['password_display'] = "*******"
            if 'encrypted_password' in r:
                del r['encrypted_password']

        return jsonify(results)
    
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


#  Search passwords (by site_name or username)
@app.route("/passwords/search/<int:user_id>", methods=["GET"])
def search_passwords(user_id):
    try:
        q = request.args.get("q", "")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM passwords 
            WHERE user_id=%s 
            AND (LOWER(site_name) LIKE LOWER(%s) OR LOWER(username) LIKE LOWER(%s)) 
            ORDER BY last_updated DESC
        """, (user_id, f"%{q}%", f"%{q}%"))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        for r in results:
            r['password_display'] = "*******"
            if 'encrypted_password' in r:
                del r['encrypted_password']

        return jsonify(results)
    
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


#  Suggest a strong password
@app.route("/passwords/suggestion", methods=["GET"])
def suggest_password():
    pwd = generate_strong_password(14)
    return jsonify({"message": "Here is a strong password suggestion ", "suggestion": pwd})





# ================== START SERVER ==================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
