from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from datetime import datetime
from config import *

app = Flask(__name__)
CORS(app)

def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# ─────────────────────────────────────
# SLOTS
# ─────────────────────────────────────

@app.route('/api/slots', methods=['GET'])
def get_slots():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM slots
        ORDER BY slot_type, level, row_num, col_num
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/slots/warehouse', methods=['GET'])
def get_warehouse_slots():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM slots WHERE slot_type='normal'
        ORDER BY level, row_num, col_num
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/slots/level/<level>', methods=['GET'])
def get_slots_by_level(level):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM slots WHERE level=%s
        ORDER BY row_num, col_num
    """, (level.upper(),))
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/slots/<level>/<int:row>/<int:col>',
           methods=['GET'])
def get_slot(level, row, col):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM slots
        WHERE level=%s AND row_num=%s AND col_num=%s
    """, (level.upper(), row, col))
    data = cursor.fetchone()
    conn.close()
    if data:
        return jsonify(data)
    return jsonify({'error': 'Slot not found'}), 404

@app.route('/api/slots/reserved', methods=['GET'])
def get_reserved_slots():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM slots WHERE slot_type='reserved'
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/slots/entry', methods=['GET'])
def get_entry_slot():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM slots WHERE slot_type='entry'
    """)
    data = cursor.fetchone()
    conn.close()
    return jsonify(data)

@app.route('/api/slots/exit', methods=['GET'])
def get_exit_slot():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM slots WHERE slot_type='exit'
    """)
    data = cursor.fetchone()
    conn.close()
    return jsonify(data)

# ─────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────

@app.route('/api/commands', methods=['GET'])
def get_commands():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM commands ORDER BY created_at DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/commands/pending', methods=['GET'])
def get_pending_commands():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM commands
        WHERE status='pending'
        ORDER BY created_at ASC
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/commands/<int:command_id>',
           methods=['GET'])
def get_command(command_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM commands WHERE id=%s
    """, (command_id,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return jsonify(data)
    return jsonify({'error': 'Command not found'}), 404

@app.route('/api/commands/retrieve', methods=['POST'])
def send_retrieve():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    level = data.get('level', '').upper()
    row   = data.get('row')
    col   = data.get('col')

    if not level or row is None or col is None:
        return jsonify(
            {'error': 'Missing level, row or col'}), 400
    if level not in ['A', 'B', 'C']:
        return jsonify(
            {'error': 'Level must be A, B or C'}), 400
    if row not in [1,2,3] or col not in [1,2,3]:
        return jsonify(
            {'error': 'Row and col must be 1, 2 or 3'}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        INSERT INTO commands
        (command_type, target_level, target_row,
         target_col, status)
        VALUES ('retrieve', %s, %s, %s, 'pending')
    """, (level, row, col))
    conn.commit()
    command_id = cursor.lastrowid
    conn.close()

    print(f"Retrieve command: {level}({row},{col})")
    return jsonify({
        'success'   : True,
        'command_id': command_id,
        'message'   : f'Retrieve command sent for '
                      f'{level}({row},{col})',
        'status'    : 'pending'
    })

@app.route('/api/commands/store', methods=['POST'])
def send_store():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    level     = data.get('level', '').upper()
    row       = data.get('row')
    col       = data.get('col')
    item_name = data.get('item_name', '')

    if not level or row is None or col is None:
        return jsonify(
            {'error': 'Missing level, row or col'}), 400
    if not item_name:
        return jsonify({'error': 'Missing item_name'}), 400
    if level not in ['A', 'B', 'C']:
        return jsonify(
            {'error': 'Level must be A, B or C'}), 400
    if row not in [1,2,3] or col not in [1,2,3]:
        return jsonify(
            {'error': 'Row and col must be 1, 2 or 3'}), 400

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        INSERT INTO commands
        (command_type, target_level, target_row,
         target_col, item_name, status)
        VALUES ('store', %s, %s, %s, %s, 'pending')
    """, (level, row, col, item_name))
    conn.commit()
    command_id = cursor.lastrowid
    conn.close()

    print(f"Store command: {item_name} -> {level}({row},{col})")
    return jsonify({
        'success'   : True,
        'command_id': command_id,
        'message'   : f'Store command sent for '
                      f'{item_name} at {level}({row},{col})',
        'status'    : 'pending'
    })

@app.route('/api/commands/<int:command_id>/sequence',
           methods=['GET'])
def get_sequence(command_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM command_sequence
        WHERE command_id=%s
        ORDER BY step_number ASC
    """, (command_id,))
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

# ─────────────────────────────────────
# LOGS
# ─────────────────────────────────────

@app.route('/api/logs', methods=['GET'])
def get_logs():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM log
        ORDER BY created_at DESC LIMIT 100
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

# ─────────────────────────────────────
# ALARMS
# ─────────────────────────────────────

@app.route('/api/alarms', methods=['GET'])
def get_alarms():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM alarms ORDER BY created_at DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/alarms/active', methods=['GET'])
def get_active_alarms():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM alarms
        WHERE resolved=FALSE
        ORDER BY created_at DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/alarms/<int:alarm_id>/resolve',
           methods=['POST'])
def resolve_alarm(alarm_id):
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE alarms
        SET resolved=TRUE, resolved_at=NOW()
        WHERE id=%s
    """, (alarm_id,))
    conn.commit()
    conn.close()
    return jsonify({
        'success': True,
        'message': 'Alarm resolved'
    })

# ─────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────

@app.route('/api/summary', methods=['GET'])
def get_summary():
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) as count FROM slots
        WHERE slot_type='normal'
    """)
    total_slots = cursor.fetchone()['count']

    cursor.execute("""
        SELECT COUNT(*) as count FROM slots
        WHERE slot_type='normal' AND status='occupied'
    """)
    occupied_slots = cursor.fetchone()['count']

    cursor.execute("""
        SELECT COUNT(*) as count FROM slots
        WHERE slot_type='normal' AND status='empty'
    """)
    empty_slots = cursor.fetchone()['count']

    cursor.execute("""
        SELECT COUNT(*) as count FROM slots
        WHERE slot_type='reserved' AND status='empty'
    """)
    reserved_available = cursor.fetchone()['count']

    cursor.execute("""
        SELECT COUNT(*) as count FROM commands
        WHERE status='pending'
    """)
    pending_commands = cursor.fetchone()['count']

    cursor.execute("""
        SELECT COUNT(*) as count FROM alarms
        WHERE resolved=FALSE
    """)
    active_alarms = cursor.fetchone()['count']

    cursor.execute("""
        SELECT * FROM slots WHERE slot_type='entry'
    """)
    entry = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM slots WHERE slot_type='exit'
    """)
    exit_slot = cursor.fetchone()

    conn.close()
    return jsonify({
        'total_slots'       : total_slots,
        'occupied_slots'    : occupied_slots,
        'empty_slots'       : empty_slots,
        'reserved_available': reserved_available,
        'pending_commands'  : pending_commands,
        'active_alarms'     : active_alarms,
        'entry_slot'        : entry,
        'exit_slot'         : exit_slot,
        'server_time'       : datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
    })

# ─────────────────────────────────────
# RUN
# ─────────────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("   WAREHOUSE FLASK API STARTING...")
    print("=" * 60)
    print("   Endpoints:")
    print("   GET  /api/slots")
    print("   GET  /api/slots/warehouse")
    print("   GET  /api/slots/level/<level>")
    print("   GET  /api/slots/reserved")
    print("   GET  /api/slots/entry")
    print("   GET  /api/slots/exit")
    print("   POST /api/commands/retrieve")
    print("   POST /api/commands/store")
    print("   GET  /api/commands")
    print("   GET  /api/commands/pending")
    print("   GET  /api/commands/<id>/sequence")
    print("   GET  /api/logs")
    print("   GET  /api/alarms")
    print("   GET  /api/alarms/active")
    print("   POST /api/alarms/<id>/resolve")
    print("   GET  /api/summary")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)