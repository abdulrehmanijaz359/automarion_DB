import sys
import os
import time
import mysql.connector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from plc_simulator import PLCSimulator
# from plc_connection import PLCConnection

class WarehouseMiddleware:
    def __init__(self):
        print("=" * 60)
        print("   WAREHOUSE MIDDLEWARE STARTING...")
        print("=" * 60)

        self.plc = PLCSimulator()
        # self.plc = PLCConnection()
        # self.plc.connect()
        print("PLC ready!")

        # Only cancel commands older than 5 minutes
        conn   = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE commands
            SET status='cancelled'
            WHERE status='pending'
            AND created_at < NOW() - INTERVAL 5 MINUTE
        """)
        conn.commit()
        conn.close()
        print("Cleared stuck old commands!")

        print("=" * 60)
        print("Listening for commands...")
        print("Press Ctrl+C to stop\n")

    # ─────────────────────────────────────
    # DATABASE
    # ─────────────────────────────────────

    def get_db(self):
        return mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

    def get_pending_commands(self):
        conn   = self.get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM commands
            WHERE status='pending'
            ORDER BY created_at ASC
        """)
        commands = cursor.fetchall()
        conn.close()
        return commands

    def reject_command(self, command_id, reason):
        conn   = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE commands
            SET status='rejected', reject_reason=%s
            WHERE id=%s
        """, (reason, command_id))
        conn.commit()
        conn.close()
        print(f"  Rejected: {reason}")

    def approve_command(self, command_id):
        conn   = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE commands SET status='approved'
            WHERE id=%s
        """, (command_id,))
        conn.commit()
        conn.close()

    def get_slot(self, level, row, col):
        conn   = self.get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM slots
            WHERE level=%s AND row_num=%s AND col_num=%s
        """, (level, row, col))
        slot = cursor.fetchone()
        conn.close()
        return slot

    def get_blocking_slots(self, level, row, col):
        blocking = []
        if level == 'A':
            slot_c = self.get_slot('C', row, col)
            slot_b = self.get_slot('B', row, col)
            if slot_c and slot_c['status'] == 'occupied':
                blocking.append(slot_c)
            if slot_b and slot_b['status'] == 'occupied':
                blocking.append(slot_b)
        elif level == 'B':
            slot_c = self.get_slot('C', row, col)
            if slot_c and slot_c['status'] == 'occupied':
                blocking.append(slot_c)
        elif level == 'C':
            pass
        return blocking

    def can_store(self, level, row, col):
        if level == 'A':
            slot = self.get_slot('A', row, col)
            if slot and slot['status'] == 'occupied':
                return False, f"A({row},{col}) is already occupied!"
            return True, "OK"
        elif level == 'B':
            slot_a = self.get_slot('A', row, col)
            slot_b = self.get_slot('B', row, col)
            if not slot_a or slot_a['status'] == 'empty':
                return False, \
                    f"Cannot store in B({row},{col}) — " \
                    f"A({row},{col}) is empty! Fill A first."
            if slot_b and slot_b['status'] == 'occupied':
                return False, f"B({row},{col}) is already occupied!"
            return True, "OK"
        elif level == 'C':
            slot_a = self.get_slot('A', row, col)
            slot_b = self.get_slot('B', row, col)
            slot_c = self.get_slot('C', row, col)
            if not slot_a or slot_a['status'] == 'empty':
                return False, \
                    f"Cannot store in C({row},{col}) — " \
                    f"A({row},{col}) is empty! Fill A first."
            if not slot_b or slot_b['status'] == 'empty':
                return False, \
                    f"Cannot store in C({row},{col}) — " \
                    f"B({row},{col}) is empty! Fill B first."
            if slot_c and slot_c['status'] == 'occupied':
                return False, f"C({row},{col}) is already occupied!"
            return True, "OK"
        return False, "Invalid level!"

    def get_reserved_slots(self):
        conn   = self.get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM slots
            WHERE slot_type='reserved' AND status='empty'
            ORDER BY row_num ASC
        """)
        slots = cursor.fetchall()
        conn.close()
        return slots

    def get_exit_slot(self):
        conn   = self.get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM slots WHERE slot_type='exit'
        """)
        slot = cursor.fetchone()
        conn.close()
        return slot

    def update_slot(self, level, row, col,
                    status, item_name=None):
        conn   = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE slots SET
                status=%s,
                item_name=%s,
                last_updated=NOW()
            WHERE level=%s AND row_num=%s AND col_num=%s
        """, (status, item_name, level, row, col))
        conn.commit()
        conn.close()

    def log(self, command_id, level, message):
        conn   = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO log (command_id, level, message)
            VALUES (%s, %s, %s)
        """, (command_id, level, message))
        conn.commit()
        conn.close()
        print(f"   [{level}] {message}")

    def mark_command(self, command_id, status):
        conn   = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE commands
            SET status=%s, completed_at=NOW()
            WHERE id=%s
        """, (status, command_id))
        conn.commit()
        conn.close()

    def create_alarm(self, alarm_type, severity, message):
        conn   = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alarms
            (alarm_type, severity, message, resolved)
            VALUES (%s, %s, %s, FALSE)
        """, (alarm_type, severity, message))
        conn.commit()
        conn.close()
        print(f"\nALARM: [{severity}] {alarm_type} — {message}")

    def save_sequence(self, steps):
        conn   = self.get_db()
        cursor = conn.cursor()
        for step in steps:
            cursor.execute("""
                INSERT INTO command_sequence
                (command_id, step_number, action,
                 from_level, from_row, from_col,
                 to_level, to_row, to_col, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                step['command_id'],
                step['step_number'],
                step['action'],
                step['from_level'],
                step['from_row'],
                step['from_col'],
                step['to_level'],
                step['to_row'],
                step['to_col'],
                step['status']
            ))
        conn.commit()
        conn.close()
        print(f"Saved {len(steps)} steps!")

    def get_steps(self, command_id):
        conn   = self.get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM command_sequence
            WHERE command_id=%s AND status='pending'
            ORDER BY step_number ASC
        """, (command_id,))
        steps = cursor.fetchall()
        conn.close()
        return steps

    def update_step(self, step_id, status):
        conn   = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE command_sequence
            SET status=%s, completed_at=NOW()
            WHERE id=%s
        """, (status, step_id))
        conn.commit()
        conn.close()

    # ─────────────────────────────────────
    # BUILD SEQUENCE
    # ─────────────────────────────────────

    def build_sequence(self, command_id, target_level,
                       target_row, target_col, blocking_slots):
        steps            = []
        step_number      = 1
        reserved_slots   = self.get_reserved_slots()
        exit_slot        = self.get_exit_slot()
        temp_assignments = []

        # PHASE 1 — Move blocking items to reserved slots
        for i, blocking in enumerate(blocking_slots):
            reserved = reserved_slots[i]

            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'HOME',
                'from_level' : None, 'from_row': None,
                'from_col'   : None, 'to_level': None,
                'to_row'     : None, 'to_col'  : None,
                'status'     : 'pending'
            })
            step_number += 1

            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'PICK',
                'from_level' : blocking['level'],
                'from_row'   : blocking['row_num'],
                'from_col'   : blocking['col_num'],
                'to_level'   : None, 'to_row': None,
                'to_col'     : None,
                'status'     : 'pending'
            })
            step_number += 1

            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'PLACE',
                'from_level' : None, 'from_row': None,
                'from_col'   : None,
                'to_level'   : reserved['level'],
                'to_row'     : reserved['row_num'],
                'to_col'     : reserved['col_num'],
                'status'     : 'pending'
            })
            step_number += 1

            temp_assignments.append({
                'original_level': blocking['level'],
                'original_row'  : blocking['row_num'],
                'original_col'  : blocking['col_num'],
                'temp_level'    : reserved['level'],
                'temp_row'      : reserved['row_num'],
                'temp_col'      : reserved['col_num'],
                'item_name'     : blocking['item_name']
            })

        # PHASE 2 — Retrieve target to EXIT
        steps.append({
            'command_id' : command_id,
            'step_number': step_number,
            'action'     : 'HOME',
            'from_level' : None, 'from_row': None,
            'from_col'   : None, 'to_level': None,
            'to_row'     : None, 'to_col'  : None,
            'status'     : 'pending'
        })
        step_number += 1

        steps.append({
            'command_id' : command_id,
            'step_number': step_number,
            'action'     : 'PICK',
            'from_level' : target_level,
            'from_row'   : target_row,
            'from_col'   : target_col,
            'to_level'   : None, 'to_row': None,
            'to_col'     : None,
            'status'     : 'pending'
        })
        step_number += 1

        steps.append({
            'command_id' : command_id,
            'step_number': step_number,
            'action'     : 'PLACE',
            'from_level' : None, 'from_row': None,
            'from_col'   : None,
            'to_level'   : exit_slot['level'],
            'to_row'     : exit_slot['row_num'],
            'to_col'     : exit_slot['col_num'],
            'status'     : 'pending'
        })
        step_number += 1

        # PHASE 3 — Return blocking items
        for temp in reversed(temp_assignments):
            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'HOME',
                'from_level' : None, 'from_row': None,
                'from_col'   : None, 'to_level': None,
                'to_row'     : None, 'to_col'  : None,
                'status'     : 'pending'
            })
            step_number += 1

            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'PICK',
                'from_level' : temp['temp_level'],
                'from_row'   : temp['temp_row'],
                'from_col'   : temp['temp_col'],
                'to_level'   : None, 'to_row': None,
                'to_col'     : None,
                'status'     : 'pending'
            })
            step_number += 1

            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'PLACE',
                'from_level' : None, 'from_row': None,
                'from_col'   : None,
                'to_level'   : temp['original_level'],
                'to_row'     : temp['original_row'],
                'to_col'     : temp['original_col'],
                'status'     : 'pending'
            })
            step_number += 1

        # FINAL HOME
        steps.append({
            'command_id' : command_id,
            'step_number': step_number,
            'action'     : 'HOME',
            'from_level' : None, 'from_row': None,
            'from_col'   : None, 'to_level': None,
            'to_row'     : None, 'to_col'  : None,
            'status'     : 'pending'
        })

        return steps

    # ─────────────────────────────────────
    # EXECUTE SEQUENCE
    # ─────────────────────────────────────

    def execute_sequence(self, command_id):
        print(f"\nExecuting sequence {command_id}...")
        print("=" * 60)

        steps = self.get_steps(command_id)

        if not steps:
            print("No steps found!")
            self.plc.reset()
            return False

        total_steps  = len(steps)
        current_item = None
        print(f"   Found {total_steps} steps\n")

        for step in steps:
            print(f"\n--- Step {step['step_number']} "
                  f"of {total_steps}: {step['action']} ---")

            # HOME
            if step['action'] == 'HOME':
                success = self.plc.send_home()
                if not success:
                    self.update_step(step['id'], 'error')
                    self.log(command_id, 'ERROR', 'HOME failed!')
                    self.mark_command(command_id, 'failed')
                    self.create_alarm(
                        'Gripper HOME Failed',
                        'critical',
                        f'Command #{command_id} — '
                        f'Gripper failed to reach HOME position!'
                    )
                    self.plc.reset()
                    return False
                self.plc.db12['gripper_status'] = GRIPPER_IDLE
                self.update_step(step['id'], 'completed')
                self.log(command_id, 'INFO', 'HOME reached')

            # PICK
            elif step['action'] == 'PICK':
                level = step['from_level']
                row   = step['from_row']
                col   = step['from_col']

                slot         = self.get_slot(level, row, col)
                current_item = slot['item_name'] if slot else None

                level_int = {
                    'A':1, 'B':2, 'C':3,
                    'R':4, 'ENTRY':0
                }.get(level, 0)

                success = self.plc.send_command(
                    ACTION_RETRIEVE, level_int, row, col
                )

                if not success:
                    self.update_step(step['id'], 'error')
                    self.log(command_id, 'ERROR',
                        f'PICK failed at {level}({row},{col})')
                    self.mark_command(command_id, 'failed')
                    self.create_alarm(
                        'Gripper PICK Failed',
                        'critical',
                        f'Command #{command_id} — '
                        f'Gripper failed to pick from '
                        f'{level}({row},{col})!'
                    )
                    self.plc.reset()
                    return False

                self.update_slot(level, row, col, 'empty')
                self.update_step(step['id'], 'completed')
                self.log(command_id, 'INFO',
                    f'Picked {current_item} '
                    f'from {level}({row},{col})')

            # PLACE
            elif step['action'] == 'PLACE':
                level = step['to_level']
                row   = step['to_row']
                col   = step['to_col']

                level_int = {
                    'A':1, 'B':2, 'C':3,
                    'R':4, 'EXIT':5
                }.get(level, 0)

                success = self.plc.send_command(
                    ACTION_STORE, level_int, row, col
                )

                if not success:
                    self.update_step(step['id'], 'error')
                    self.log(command_id, 'ERROR',
                        f'PLACE failed at {level}({row},{col})')
                    self.mark_command(command_id, 'failed')
                    self.create_alarm(
                        'Gripper PLACE Failed',
                        'critical',
                        f'Command #{command_id} — '
                        f'Gripper failed to place at '
                        f'{level}({row},{col})!'
                    )
                    self.plc.reset()
                    return False

                if level != 'EXIT':
                    self.update_slot(
                        level, row, col,
                        'occupied', current_item
                    )

                self.update_step(step['id'], 'completed')
                self.log(command_id, 'INFO',
                    f'Placed {current_item} '
                    f'at {level}({row},{col})')

        self.mark_command(command_id, 'completed')
        self.plc.reset()
        print("\n" + "=" * 60)
        print("Completed! Ready for next command!\n")
        return True

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

        print(f"\nNew command #{command_id}")
        print(f"   Type  : {command_type.upper()}")
        print(f"   Target: {level}({row},{col})")
        if item_name:
            print(f"   Item  : {item_name}")

        # RETRIEVE
        if command_type == 'retrieve':
            blocking_slots = self.get_blocking_slots(level, row, col)
            reserved       = self.get_reserved_slots()

            if len(blocking_slots) > len(reserved):
                self.reject_command(
                    command_id,
                    f"Not enough reserved slots! "
                    f"Need {len(blocking_slots)}, "
                    f"have {len(reserved)}"
                )
                return

            slot = self.get_slot(level, row, col)
            if not slot or slot['status'] == 'empty':
                self.reject_command(
                    command_id,
                    f"Slot {level}({row},{col}) is already empty!"
                )
                return

            self.approve_command(command_id)
            steps = self.build_sequence(
                command_id, level, row, col, blocking_slots
            )
            self.save_sequence(steps)
            self.execute_sequence(command_id)

        # STORE
        elif command_type == 'store':
            can, reason = self.can_store(level, row, col)
            if not can:
                self.reject_command(command_id, reason)
                return

            slot = self.get_slot(level, row, col)
            if slot and slot['slot_type'] == 'reserved':
                self.reject_command(
                    command_id,
                    f"Slot {level}({row},{col}) is reserved!"
                )
                return

            self.approve_command(command_id)

            steps = [
                {
                    'command_id' : command_id,
                    'step_number': 1,
                    'action'     : 'HOME',
                    'from_level' : None, 'from_row': None,
                    'from_col'   : None, 'to_level': None,
                    'to_row'     : None, 'to_col'  : None,
                    'status'     : 'pending'
                },
                {
                    'command_id' : command_id,
                    'step_number': 2,
                    'action'     : 'PICK',
                    'from_level' : 'ENTRY',
                    'from_row'   : 0,
                    'from_col'   : 0,
                    'to_level'   : None, 'to_row': None,
                    'to_col'     : None,
                    'status'     : 'pending'
                },
                {
                    'command_id' : command_id,
                    'step_number': 3,
                    'action'     : 'HOME',
                    'from_level' : None, 'from_row': None,
                    'from_col'   : None, 'to_level': None,
                    'to_row'     : None, 'to_col'  : None,
                    'status'     : 'pending'
                },
                {
                    'command_id' : command_id,
                    'step_number': 4,
                    'action'     : 'PLACE',
                    'from_level' : None, 'from_row': None,
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
                    'from_level' : None, 'from_row': None,
                    'from_col'   : None, 'to_level': None,
                    'to_row'     : None, 'to_col'  : None,
                    'status'     : 'pending'
                }
            ]

            self.save_sequence(steps)

            conn   = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE slots SET item_name=%s
                WHERE slot_type='entry'
            """, (item_name,))
            conn.commit()
            conn.close()

            success = self.execute_sequence(command_id)

            if success:
                self.update_slot(
                    level, row, col, 'occupied', item_name
                )
                print(f"\nStored {item_name} at {level}({row},{col})")
            else:
                print(f"\nStore failed!")

    # ─────────────────────────────────────
    # MAIN LOOP
    # ─────────────────────────────────────

    def run(self):
        try:
            while True:
                try:
                    commands = self.get_pending_commands()
                    if commands:
                        for command in commands:
                            self.process_command(command)
                    else:
                        print(".", end="", flush=True)

                except Exception as e:
                    print(f"\nError: {e}")
                    print("Continuing...")

                time.sleep(LOOP_INTERVAL)

        except KeyboardInterrupt:
            print("\n\nStopped!")
            self.cleanup()

    def cleanup(self):
        try:
            self.plc.disconnect()
            print("Goodbye!")
        except:
            pass

if __name__ == '__main__':
    middleware = WarehouseMiddleware()
    middleware.run()