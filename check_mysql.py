import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        port=3306
    )
    print("Connected!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")