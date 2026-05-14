import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='automation_db'
)
cursor = conn.cursor()

# Test retrieve command
cursor.execute("""
    INSERT INTO commands
    (command_type, target_level, target_row, target_col)
    VALUES ('retrieve', 'A', 2, 2)
""")
conn.commit()
print("✅ Retrieve command sent!")

# Test store command
cursor.execute("""
    INSERT INTO commands
    (command_type, target_level, target_row,
     target_col, item_name)
    VALUES ('store', 'B', 1, 1, 'New Motor')
""")
conn.commit()
print("✅ Store command sent!")

conn.close()