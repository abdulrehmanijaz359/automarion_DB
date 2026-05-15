import mysql.connector
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from datetime import datetime

class CommandExecutor:
    def __init__(self, plc):
        # plc can be PLCSimulator OR real PLCConnection
        # works the same way for both!
        self.plc = plc
        self.conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def log(self, command_id, level, message):
        self.cursor.execute("""
            INSERT INTO log (command_id, level, message)
            VALUES (%s, %s, %s)
        """, (command_id, level, message))
        self.conn.commit()
        print(f"   📝 [{level}] {message}")

    def update_step(self, step_id, status):
        self.cursor.execute("""
            UPDATE command_sequence
            SET status=%s, completed_at=%s
            WHERE id=%s
        """, (status, datetime.now(), step_id))
        self.conn.commit()

    def update_slot(self, level, row, col, status, item_name=None,
                    is_temporary=False, orig_level=None,
                    orig_row=None, orig_col=None):
        self.cursor.execute("""
            UPDATE slots SET
                status=%s,
                item_name=%s,
                is_temporary=%s,
                original_level=%s,
                original_row=%s,
                original_col=%s,
                last_updated=%s
            WHERE level=%s AND row_num=%s AND col_num=%s
        """, (
            status, item_name, is_temporary,
            orig_level, orig_row, orig_col,
            datetime.now(), level, row, col
        ))
        self.conn.commit()

    def get_slot_item(self, level, row, col):
        self.cursor.execute("""
            SELECT item_name FROM slots
            WHERE level=%s AND row_num=%s AND col_num=%s
        """, (level, row, col))
        result = self.cursor.fetchone()
        return result['item_name'] if result else None

    def execute_sequence(self, command_id):
        print(f"\n🚀 Executing command sequence {command_id}...")
        print("=" * 60)

        # Get all pending steps for this command
        self.cursor.execute("""
            SELECT * FROM command_sequence
            WHERE command_id=%s AND status='pending'
            ORDER BY step_number ASC
        """, (command_id,))
        steps = self.cursor.fetchall()

        if not steps:
            print("❌ No pending steps found!")
            return False

        print(f"   Found {len(steps)} steps to execute\n")
        current_item = None

        for step in steps:
            print(f"\n--- Step {step['step_number']} of {len(steps)}: {step['action']} ---")

            # ─────────────────────────────
            # HOME
            # ─────────────────────────────
            if step['action'] == 'HOME':
                success = self.plc.send_home()
                if not success:
                    self.update_step(step['id'], 'error')
                    self.log(command_id, 'ERROR', 'HOME command failed!')
                    return False

                # After home, gripper status goes to IDLE
                self.plc.db12['gripper_status'] = GRIPPER_IDLE
                self.update_step(step['id'], 'completed')
                self.log(command_id, 'INFO', 'Gripper reached HOME')

            # ─────────────────────────────
            # PICK
            # ─────────────────────────────
            elif step['action'] == 'PICK':
                level = step['from_level']
                row   = step['from_row']
                col   = step['from_col']

                # Get item name from database
                current_item = self.get_slot_item(level, row, col)

                # Convert level to integer for PLC
                level_int = {'A':1, 'B':2, 'C':3, 'R':4}.get(level, 0)

                # Send pick command to PLC
                success = self.plc.send_command(
                    ACTION_RETRIEVE, level_int, row, col
                )

                if not success:
                    self.update_step(step['id'], 'error')
                    self.log(command_id, 'ERROR',
                        f'PICK failed at {level}({row},{col})')
                    return False

                # Update slot to empty in database
                self.update_slot(level, row, col, 'empty')
                self.update_step(step['id'], 'completed')
                self.log(command_id, 'INFO',
                    f'Picked {current_item} from {level}({row},{col})')

            # ─────────────────────────────
            # PLACE
            # ─────────────────────────────
            elif step['action'] == 'PLACE':
                level = step['to_level']
                row   = step['to_row']
                col   = step['to_col']

                # Convert level to integer for PLC
                
                level_int = {'A':1, 'B':2, 'C':3, 'R':4}.get(level, 0)

                # Send place command to PLC
                success = self.plc.send_command(
                    ACTION_STORE, level_int, row, col
                )

                if not success:
                    self.update_step(step['id'], 'error')
                    self.log(command_id, 'ERROR',
                        f'PLACE failed at {level}({row},{col})')
                    return False

                # Update slot to occupied in database
                if level != 'EXIT':
                    self.update_slot(level, row, col,
                        'occupied', current_item)

                self.update_step(step['id'], 'completed')
                self.log(command_id, 'INFO',
                    f'Placed {current_item} at {level}({row},{col})')

        # All steps done!
        self.cursor.execute("""
            UPDATE commands
            SET status='completed', completed_at=%s
            WHERE id=%s
        """, (datetime.now(), command_id))
        self.conn.commit()

        print("\n" + "=" * 60)
        print("🎉 Command sequence completed successfully!")
        return True