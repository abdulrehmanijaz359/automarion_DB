import mysql.connector
import time

print("Starting setup...")
time.sleep(1)

# Connect without database first
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password=''
)
cursor = conn.cursor()

# Create database
cursor.execute("CREATE DATABASE IF NOT EXISTS automation_db")
cursor.execute("USE automation_db")
print("Database created!")
time.sleep(1)

# Create tables
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
print("slots table created!")

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
print("commands table created!")

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
print("command_sequence table created!")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS log (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        command_id INT DEFAULT NULL,
        level      VARCHAR(10) DEFAULT NULL,
        message    TEXT,
        created_at DATETIME DEFAULT NOW()
    )
""")
print("log table created!")

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
print("alarms table created!")

conn.commit()
print("All tables done!")
time.sleep(1)

# Now populate slots
cursor.execute("DELETE FROM slots")
print("Cleared old slots!")

# 27 normal slots
levels = ['A', 'B', 'C']
for level in levels:
    for row in range(1, 4):
        for col in range(1, 4):
            cursor.execute("""
                INSERT INTO slots
                (level, row_num, col_num, slot_type, status)
                VALUES (%s, %s, %s, 'normal', 'empty')
            """, (level, row, col))
print("27 normal slots created!")

# 3 reserved slots
for i in range(1, 4):
    cursor.execute("""
        INSERT INTO slots
        (level, row_num, col_num, slot_type, status)
        VALUES ('R', %s, 0, 'reserved', 'empty')
    """, (i,))
print("3 reserved slots created!")

# Entry slot
cursor.execute("""
    INSERT INTO slots
    (level, row_num, col_num, slot_type, status)
    VALUES ('ENTRY', 0, 0, 'entry', 'empty')
""")
print("Entry slot created!")

# Exit slot
cursor.execute("""
    INSERT INTO slots
    (level, row_num, col_num, slot_type, status)
    VALUES ('EXIT', 0, 0, 'exit', 'empty')
""")
print("Exit slot created!")

conn.commit()
conn.close()

print("")
print("================================")
print("ALL DONE! 32 slots created!")
print("  27 normal slots")
print("   3 reserved slots")
print("   1 entry slot")
print("   1 exit slot")
print("================================")
input("Press Enter to close...")