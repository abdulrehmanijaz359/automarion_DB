import sys
sys.path.append('middleware')
from plc_simulator import PLCSimulator
from blocking_logic import BlockingLogic
from relocation import Relocation
from command_executor import CommandExecutor
import mysql.connector
from config import *

# Setup
plc  = PLCSimulator()
bl   = BlockingLogic()
rel  = Relocation()
exec = CommandExecutor(plc)

# Create a test command in database
conn = mysql.connector.connect(
    host=DB_HOST, user=DB_USER,
    password=DB_PASSWORD, database=DB_NAME
)
cursor = conn.cursor(dictionary=True)

cursor.execute("""
    INSERT INTO commands
    (command_type, target_level, target_row, target_col, status)
    VALUES ('retrieve', 'A', 2, 2, 'approved')
""")
conn.commit()
command_id = cursor.lastrowid
conn.close()

print(f"✅ Created command ID: {command_id}")

# Check blocking
accessible, blocking, message = bl.check_access('A', 2, 2)
print(f"🔍 Blocking check: {message}")

# Build sequence
steps, temp = rel.build_sequence(
    command_id, 'A', 2, 2, blocking
)
rel.save_sequence(steps)

# Execute!
exec.execute_sequence(command_id)