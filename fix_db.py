import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='automation_db'
)
cursor = conn.cursor()

# Drop old unused tables
cursor.execute("DROP TABLE IF EXISTS cargo")
cursor.execute("DROP TABLE IF EXISTS inventory")
cursor.execute("DROP TABLE IF EXISTS machine_status")
cursor.execute("DROP TABLE IF EXISTS sensor_data")
print("Old tables removed!")

# Show remaining tables
cursor.execute("SHOW TABLES")
print("\nTables remaining:")
for table in cursor.fetchall():
    print(f"  -> {table[0]}")

# Count slots
cursor.execute("SELECT COUNT(*) FROM slots")
print(f"\nTotal slots: {cursor.fetchone()[0]}")

conn.commit()
conn.close()
print("\nDone!")
