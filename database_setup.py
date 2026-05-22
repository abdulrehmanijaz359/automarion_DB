import mysql.connector
from config import *

conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = conn.cursor()

cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
cursor.execute(f"USE {DB_NAME}")
print("✅ Database created!")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS slots (
        id             INT AUTO_INCREMENT PRIMARY KEY,
        level          VARCHAR(10),
        row_num        INT,
        col_num        INT,
        slot_type      VARCHAR(20) DEFAULT 'normal',
        status         VARCHAR(20) DEFAULT 'empty',
        item_name      VARCHAR(50) DEFAULT NULL,
        is_temporary   BOOLEAN DEFAULT FALSE,
        original_level VARCHAR(10) DEFAULT NULL,
        original_row   INT DEFAULT NULL,
        original_col   INT DEFAULT NULL,
        last_updated   DATETIME DEFAULT NOW()
    )
""")
print("✅ slots table created!")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS commands (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        command_type  VARCHAR(20),
        target_level  VARCHAR(10),
        target_row    INT,
        target_col    INT,
        item_name     VARCHAR(50) DEFAULT NULL,
        status        VARCHAR(20) DEFAULT 'pending',
        reject_reason TEXT DEFAULT NULL,
        created_at    DATETIME DEFAULT NOW(),
        completed_at  DATETIME DEFAULT NULL
    )
""")
print("✅ commands table created!")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS command_sequence (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        command_id   INT,
        step_number  INT,
        action       VARCHAR(20),
        from_level   VARCHAR(10) DEFAULT NULL,
        from_row     INT DEFAULT NULL,
        from_col     INT DEFAULT NULL,
        to_level     VARCHAR(10) DEFAULT NULL,
        to_row       INT DEFAULT NULL,
        to_col       INT DEFAULT NULL,
        status       VARCHAR(20) DEFAULT 'pending',
        created_at   DATETIME DEFAULT NOW(),
        completed_at DATETIME DEFAULT NULL
    )
""")
print("✅ command_sequence table created!")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS log (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        command_id INT DEFAULT NULL,
        level      VARCHAR(10) DEFAULT NULL,
        message    TEXT,
        created_at DATETIME DEFAULT NOW()
    )
""")
print("✅ log table created!")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS alarms (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        alarm_type  VARCHAR(50),
        severity    VARCHAR(20),
        message     TEXT,
        resolved    BOOLEAN DEFAULT FALSE,
        created_at  DATETIME DEFAULT NOW(),
        resolved_at DATETIME DEFAULT NULL
    )
""")
print("✅ alarms table created!")

conn.commit()
conn.close()
print("\n🎉 All tables created!")