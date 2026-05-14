import mysql.connector
from config import *

conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

cursor = conn.cursor()

# Clear existing slots
cursor.execute("DELETE FROM slots")
print("🗑️ Cleared existing slots!")

# ─────────────────────────────────────────
# 27 NORMAL warehouse slots
# ─────────────────────────────────────────
levels = ['A', 'B', 'C']
for level in levels:
    for row in range(1, 4):
        for col in range(1, 4):
            cursor.execute("""
                INSERT INTO slots (level, row_num, col_num, slot_type, status)
                VALUES (%s, %s, %s, 'normal', 'empty')
            """, (level, row, col))

print("✅ 27 normal slots created!")

# ─────────────────────────────────────────
# 3 RESERVED slots (outside warehouse)
# ─────────────────────────────────────────
for i in range(1, 4):
    cursor.execute("""
        INSERT INTO slots (level, row_num, col_num, slot_type, status)
        VALUES ('R', %s, 0, 'reserved', 'empty')
    """, (i,))

print("✅ 3 reserved slots created!")

# ─────────────────────────────────────────
# 1 ENTRY slot
# ─────────────────────────────────────────
cursor.execute("""
    INSERT INTO slots (level, row_num, col_num, slot_type, status)
    VALUES ('ENTRY', 0, 0, 'entry', 'empty')
""")
print("✅ Entry slot created!")

# ─────────────────────────────────────────
# 1 EXIT slot
# ─────────────────────────────────────────
cursor.execute("""
    INSERT INTO slots (level, row_num, col_num, slot_type, status)
    VALUES ('EXIT', 0, 0, 'exit', 'empty')
""")
print("✅ Exit slot created!")

conn.commit()
conn.close()

print("\n🎉 All 32 slots populated!")
print("   27 normal slots")
print("    3 reserved slots")
print("    1 entry slot")
print("    1 exit slot")
print("  ─────────────────")
print("   32 total slots")