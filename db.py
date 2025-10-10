import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="younsi", 
        database="password_guardian",
        port=3306
    )
