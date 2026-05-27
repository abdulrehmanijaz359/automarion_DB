import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='automation_db'
)
cursor = conn.cursor()

# Count by type
cursor.execute("""
    SELECT slot_type, COUNT(*) as count
    FROM slots
    GROUP BY slot_type
""")
print("Slots by type:")
for row in cursor.fetchall():
    print(f"  {row[0]} -> {row[1]}")

# Show all normal slots
cursor.execute("""
    SELECT level, row_num, col_num, status, item_name
    FROM slots
    WHERE slot_type='normal'
    ORDER BY level, row_num, col_num
""")
print("\nNormal slots:")
for row in cursor.fetchall():
    print(f"  {row[0]}({row[1]},{row[2]}) "
          f"-> {row[3]} "
          f"{'| ' + row[4] if row[4] else ''}")

# Show reserved slots
cursor.execute("""
    SELECT level, row_num, col_num, status
    FROM slots WHERE slot_type='reserved'
""")
print("\nReserved slots:")
for row in cursor.fetchall():
    print(f"  R({row[1]},{row[2]}) -> {row[3]}")

# Show entry and exit
cursor.execute("""
    SELECT level, slot_type, status, item_name
    FROM slots
    WHERE slot_type IN ('entry','exit')
""")
print("\nEntry/Exit slots:")
for row in cursor.fetchall():
    print(f"  {row[0]} ({row[1]}) -> {row[2]}")

conn.close()
print("\nDatabase looks good!")