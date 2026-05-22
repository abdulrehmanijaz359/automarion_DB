# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

# PLC Settings
PLC_IP   = '192.168.0.1'  # change to real IP
PLC_RACK = 0
PLC_SLOT = 1

# DB11 — Commands (we write TO this)
DB_COMMAND    = 11
OFFSET_ACTION = 0
OFFSET_LEVEL  = 2
OFFSET_ROW    = 4
OFFSET_COL    = 6

# DB12 — Status (we read FROM this)
DB_STATUS         = 12
OFFSET_GRIPPER    = 0
OFFSET_CURR_LEVEL = 2
OFFSET_CURR_ROW   = 4
OFFSET_CURR_COL   = 6

# Action integers
ACTION_HOME     = 0
ACTION_RETRIEVE = 1
ACTION_STORE    = 2

# Level integers
LEVEL_A = 1
LEVEL_B = 2
LEVEL_C = 3

# Gripper status integers
GRIPPER_IDLE   = 0
GRIPPER_MOVING = 1
GRIPPER_DONE   = 2
GRIPPER_ERROR  = 3

# Database Settings
DB_HOST     = 'localhost'
DB_USER     = 'root'
DB_PASSWORD = ''
DB_NAME     = 'automation_db'

# Slot types
SLOT_NORMAL   = 'normal'
SLOT_RESERVED = 'reserved'
SLOT_ENTRY    = 'entry'
SLOT_EXIT     = 'exit'

# Timing
POLL_INTERVAL   = 0.5
COMMAND_TIMEOUT = 30
LOOP_INTERVAL   = 1