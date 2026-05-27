import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='automation_db'
)
cursor = conn.cursor()

# Drop old alarms table
cursor.execute("DROP TABLE IF EXISTS alarms")
print("Old alarms table dropped!")

# Create correct alarms table
cursor.execute("""
    CREATE TABLE alarms (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        alarm_type  VARCHAR(50),
        severity    VARCHAR(20),
        message     TEXT,
        resolved    BOOLEAN DEFAULT FALSE,
        created_at  DATETIME DEFAULT NOW(),
        resolved_at DATETIME DEFAULT NULL
    )
""")
print("New alarms table created!")

conn.commit()
conn.close()
print("Done!")