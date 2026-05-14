import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='automation_db'
)
cursor = conn.cursor()

# Drop old tables
cursor.execute("DROP TABLE IF EXISTS command_sequence")
cursor.execute("DROP TABLE IF EXISTS commands")
print("Dropped old tables!")

# Create new commands table
cursor.execute("""
    CREATE TABLE commands (
        id INT AUTO_INCREMENT PRIMARY KEY,
        command_type VARCHAR(20),
        target_level VARCHAR(10),
        target_row INT,
        target_col INT,
        item_name VARCHAR(50) DEFAULT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        reject_reason TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT NOW(),
        completed_at DATETIME DEFAULT NULL
    )
""")
print("commands table created!")

# Create new command_sequence table
cursor.execute("""
    CREATE TABLE command_sequence (
        id INT AUTO_INCREMENT PRIMARY KEY,
        command_id INT,
        step_number INT,
        action VARCHAR(20),
        from_level VARCHAR(10) DEFAULT NULL,
        from_row INT DEFAULT NULL,
        from_col INT DEFAULT NULL,
        to_level VARCHAR(10) DEFAULT NULL,
        to_row INT DEFAULT NULL,
        to_col INT DEFAULT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at DATETIME DEFAULT NOW(),
        completed_at DATETIME DEFAULT NULL
    )
""")
print("command_sequence table created!")

conn.commit()
conn.close()
print("Done!")