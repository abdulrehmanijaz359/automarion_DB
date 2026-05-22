import mysql.connector
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

class Relocation:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def get_reserved_slots(self):
        self.cursor.execute("""
            SELECT * FROM slots
            WHERE slot_type='reserved' AND status='empty'
            ORDER BY row_num ASC
        """)
        return self.cursor.fetchall()

    def get_exit_slot(self):
        self.cursor.execute("""
            SELECT * FROM slots WHERE slot_type='exit'
        """)
        return self.cursor.fetchone()

    def build_sequence(self, command_id, target_level,
                       target_row, target_col, blocking_slots):
        steps          = []
        step_number    = 1
        reserved_slots = self.get_reserved_slots()
        exit_slot      = self.get_exit_slot()
        temp_assignments = []

        # PHASE 1 — Move blocking items to reserved slots
        for i, blocking in enumerate(blocking_slots):
            reserved = reserved_slots[i]

            # HOME
            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'HOME',
                'from_level' : None, 'from_row': None, 'from_col': None,
                'to_level'   : None, 'to_row'  : None, 'to_col'  : None,
                'status'     : 'pending'
            })
            step_number += 1

            # PICK blocking item
            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'PICK',
                'from_level' : blocking['level'],
                'from_row'   : blocking['row_num'],
                'from_col'   : blocking['col_num'],
                'to_level'   : None, 'to_row': None, 'to_col': None,
                'status'     : 'pending'
            })
            step_number += 1

            # PLACE in reserved slot
            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'PLACE',
                'from_level' : None, 'from_row': None, 'from_col': None,
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

        # PHASE 2 — Retrieve target item to EXIT
        steps.append({
            'command_id' : command_id,
            'step_number': step_number,
            'action'     : 'HOME',
            'from_level' : None, 'from_row': None, 'from_col': None,
            'to_level'   : None, 'to_row'  : None, 'to_col'  : None,
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
            'to_level'   : None, 'to_row': None, 'to_col': None,
            'status'     : 'pending'
        })
        step_number += 1

        steps.append({
            'command_id' : command_id,
            'step_number': step_number,
            'action'     : 'PLACE',
            'from_level' : None, 'from_row': None, 'from_col': None,
            'to_level'   : exit_slot['level'],
            'to_row'     : exit_slot['row_num'],
            'to_col'     : exit_slot['col_num'],
            'status'     : 'pending'
        })
        step_number += 1

        # PHASE 3 — Return blocking items to original positions
        for temp in reversed(temp_assignments):
            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'HOME',
                'from_level' : None, 'from_row': None, 'from_col': None,
                'to_level'   : None, 'to_row'  : None, 'to_col'  : None,
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
                'to_level'   : None, 'to_row': None, 'to_col': None,
                'status'     : 'pending'
            })
            step_number += 1

            steps.append({
                'command_id' : command_id,
                'step_number': step_number,
                'action'     : 'PLACE',
                'from_level' : None, 'from_row': None, 'from_col': None,
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
            'from_level' : None, 'from_row': None, 'from_col': None,
            'to_level'   : None, 'to_row'  : None, 'to_col'  : None,
            'status'     : 'pending'
        })

        return steps, temp_assignments

    def save_sequence(self, steps):
        for step in steps:
            self.cursor.execute("""
                INSERT INTO command_sequence
                (command_id, step_number, action,
                 from_level, from_row, from_col,
                 to_level, to_row, to_col, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                step['command_id'],
                step['step_number'],
                step['action'],
                step['from_level'], step['from_row'], step['from_col'],
                step['to_level'],   step['to_row'],   step['to_col'],
                step['status']
            ))
        self.conn.commit()
        print(f"✅ Saved {len(steps)} steps to database!")