import sys
import os
import time
import mysql.connector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from plc_simulator import PLCSimulator
# from plc_connection import PLCConnection
from blocking_logic import BlockingLogic
from relocation import Relocation
from command_executor import CommandExecutor

class WarehouseMiddleware:
    def __init__(self):
        print("=" * 60)
        print("   🏭 WAREHOUSE MIDDLEWARE STARTING...")
        print("=" * 60)

        # Connect to database
        self.conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        self.cursor = self.conn.cursor(dictionary=True)
        print("✅ Database connected!")

        # Start PLC simulator
        self.plc = PLCSimulator()
        # self.plc = PLCConnection()
        # self.plc.connect()

        # Initialize modules
        self.blocking   = BlockingLogic()
        self.relocation = Relocation()
        self.executor   = CommandExecutor(self.plc)
        print("✅ All modules loaded!")

        # Only cancel commands older than 5 minutes
        # These are stuck from a previous crash
        self.cursor.execute("""
            UPDATE commands
            SET status='cancelled'
            WHERE status='pending'
            AND created_at < NOW() - INTERVAL 5 MINUTE
        """)
        self.conn.commit()
        print("🧹 Cleared stuck old commands!")

        print("=" * 60)
        print("👂 Listening for commands...")
        print("   Press Ctrl+C to stop\n")

    # ─────────────────────────────────────
    # DATABASE HELPERS
    # ─────────────────────────────────────

    def get_pending_commands(self):
        self.cursor.execute("""
            SELECT * FROM commands
            WHERE status='pending'
            ORDER BY created_at ASC
        """)
        return self.cursor.fetchall()

    def reject_command(self, command_id, reason):
        self.cursor.execute("""
            UPDATE commands
            SET status='rejected', reject_reason=%s
            WHERE id=%s
        """, (reason, command_id))
        self.conn.commit()
        print(f"  ❌ Command {command_id} rejected: {reason}")

    def approve_command(self, command_id):
        self.cursor.execute("""
            UPDATE commands
            SET status='approved'
            WHERE id=%s
        """, (command_id,))
        self.conn.commit()

    # ─────────────────────────────────────
    # PROCESS COMMAND
    # ─────────────────────────────────────

    def process_command(self, command):
        command_id   = command['id']
        command_type = command['command_type']
        level        = command['target_level']
        row          = command['target_row']
        col          = command['target_col']
        item_name    = command['item_name']

        print(f"\n📬 New command #{command_id}")
        print(f"   Type  : {command_type.upper()}")
        print(f"   Target: {level}({row},{col})")
        if item_name:
            print(f"   Item  : {item_name}")

        # ─────────────────────────────
        # RETRIEVE
        # ─────────────────────────────
        if command_type == 'retrieve':

            # Check blocking
            accessible, blocking_slots, message = \
                self.blocking.check_access(level, row, col)

            print(f"   🔍 Blocking check: {message}")

            if not accessible:
                self.reject_command(command_id, message)
                return

            # Check if slot has item
            self.cursor.execute("""
                SELECT * FROM slots
                WHERE level=%s AND row_num=%s AND col_num=%s
            """, (level, row, col))
            slot = self.cursor.fetchone()

            if not slot or slot['status'] == 'empty':
                self.reject_command(
                    command_id,
                    f"Slot {level}({row},{col}) is already empty!"
                )
                return

            # Approve and build sequence
            self.approve_command(command_id)

            steps, temp = self.relocation.build_sequence(
                command_id, level, row, col, blocking_slots
            )
            self.relocation.save_sequence(steps)

            # Execute
            success = self.executor.execute_sequence(command_id)

            if success:
                print(f"\n✅ Retrieved {slot['item_name']} "
                      f"from {level}({row},{col})")
            else:
                print(f"\n❌ Retrieval failed!")

        # ─────────────────────────────
        # STORE
        # ─────────────────────────────
        elif command_type == 'store':

            # Check stacking rules
            can, reason = self.blocking.can_store(level, row, col)

            if not can:
                self.reject_command(command_id, reason)
                return

            # Check if reserved slot
            self.cursor.execute("""
                SELECT * FROM slots
                WHERE level=%s AND row_num=%s AND col_num=%s
            """, (level, row, col))
            slot = self.cursor.fetchone()

            if slot and slot['slot_type'] == 'reserved':
                self.reject_command(
                    command_id,
                    f"Slot {level}({row},{col}) is a reserved slot!"
                )
                return

            # Approve command
            self.approve_command(command_id)

            # Build store sequence
            steps = [
                {
                    'command_id' : command_id,
                    'step_number': 1,
                    'action'     : 'HOME',
                    'from_level' : None,
                    'from_row'   : None,
                    'from_col'   : None,
                    'to_level'   : None,
                    'to_row'     : None,
                    'to_col'     : None,
                    'status'     : 'pending'
                },
                {
                    'command_id' : command_id,
                    'step_number': 2,
                    'action'     : 'PICK',
                    'from_level' : 'ENTRY',
                    'from_row'   : 0,
                    'from_col'   : 0,
                    'to_level'   : None,
                    'to_row'     : None,
                    'to_col'     : None,
                    'status'     : 'pending'
                },
                {
                    'command_id' : command_id,
                    'step_number': 3,
                    'action'     : 'HOME',
                    'from_level' : None,
                    'from_row'   : None,
                    'from_col'   : None,
                    'to_level'   : None,
                    'to_row'     : None,
                    'to_col'     : None,
                    'status'     : 'pending'
                },
                {
                    'command_id' : command_id,
                    'step_number': 4,
                    'action'     : 'PLACE',
                    'from_level' : None,
                    'from_row'   : None,
                    'from_col'   : None,
                    'to_level'   : level,
                    'to_row'     : row,
                    'to_col'     : col,
                    'status'     : 'pending'
                },
                {
                    'command_id' : command_id,
                    'step_number': 5,
                    'action'     : 'HOME',
                    'from_level' : None,
                    'from_row'   : None,
                    'from_col'   : None,
                    'to_level'   : None,
                    'to_row'     : None,
                    'to_col'     : None,
                    'status'     : 'pending'
                }
            ]

            self.relocation.save_sequence(steps)

            # Update entry slot item name
            self.cursor.execute("""
                UPDATE slots SET item_name=%s
                WHERE slot_type='entry'
            """, (item_name,))
            self.conn.commit()

            # Execute
            success = self.executor.execute_sequence(command_id)

            if success:
                self.cursor.execute("""
                    UPDATE slots
                    SET status='occupied', item_name=%s
                    WHERE level=%s AND row_num=%s AND col_num=%s
                """, (item_name, level, row, col))
                self.conn.commit()
                print(f"\n✅ Stored {item_name} at {level}({row},{col})")
            else:
                print(f"\n❌ Store failed!")

    # ─────────────────────────────────────
    # MAIN LOOP
    # ─────────────────────────────────────

    def run(self):
        try:
            while True:
                try:
                    # Check for new pending commands
                    commands = self.get_pending_commands()

                    if commands:
                        for command in commands:
                            self.process_command(command)
                    else:
                        print(".", end="", flush=True)

                except mysql.connector.Error as e:
                    print(f"\n❌ Database error: {e}")
                    print("🔄 Reconnecting to database...")
                    try:
                        self.conn = mysql.connector.connect(
                            host=DB_HOST,
                            user=DB_USER,
                            password=DB_PASSWORD,
                            database=DB_NAME
                        )
                        self.cursor = self.conn.cursor(dictionary=True)
                        print("✅ Reconnected!")
                    except:
                        print("❌ Reconnect failed — retrying in 5s...")
                        time.sleep(5)

                except Exception as e:
                    print(f"\n❌ Unexpected error: {e}")
                    print("🔄 Continuing loop...")

                time.sleep(LOOP_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n🛑 Middleware stopped by user!")
            self.cleanup()

    # ─────────────────────────────────────
    # CLEANUP
    # ─────────────────────────────────────

    def cleanup(self):
        try:
            self.plc.disconnect()
            self.conn.close()
            print("👋 Goodbye!")
        except:
            pass

# ─────────────────────────────────────
# RUN
# ─────────────────────────────────────

if __name__ == '__main__':
    middleware = WarehouseMiddleware()
    middleware.run()