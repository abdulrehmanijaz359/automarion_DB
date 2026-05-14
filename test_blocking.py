import sys
sys.path.append('middleware')
from blocking_logic import BlockingLogic
import mysql.connector
from config import *

# First add some test data
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = conn.cursor()

# Simulate B(2,2) and C(2,2) occupied
cursor.execute("""
    UPDATE slots SET status='occupied', item_name='Steel Box'
    WHERE level='B' AND row_num=2 AND col_num=2
""")
cursor.execute("""
    UPDATE slots SET status='occupied', item_name='Motor Unit'
    WHERE level='C' AND row_num=2 AND col_num=2
""")
conn.commit()
conn.close()

# Test blocking logic
bl = BlockingLogic()

print("\n🧪 TEST 1 — Retrieve A(2,2) — should need relocation")
accessible, blocking, message = bl.check_access('A', 2, 2)
print(f"   Accessible: {accessible}")
print(f"   Blocking slots: {[(s['level'], s['row_num'], s['col_num']) for s in blocking]}")
print(f"   Message: {message}")

print("\n🧪 TEST 2 — Retrieve C(1,1) — should be accessible")
accessible, blocking, message = bl.check_access('C', 1, 1)
print(f"   Accessible: {accessible}")
print(f"   Message: {message}")

print("\n🧪 TEST 3 — Retrieve B(2,2) — should need relocation")
accessible, blocking, message = bl.check_access('B', 2, 2)
print(f"   Accessible: {accessible}")
print(f"   Blocking slots: {[(s['level'], s['row_num'], s['col_num']) for s in blocking]}")
print(f"   Message: {message}")