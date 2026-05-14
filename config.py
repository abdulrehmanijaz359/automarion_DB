# ─────────────────────────────────────────
# CONFIG — change these after meeting
# ─────────────────────────────────────────

# PLC Settings
PLC_IP   = '192.168.0.1'  # change to real IP
PLC_RACK = 0
PLC_SLOT = 1

# DB11 — Commands (we write TO this)
DB_COMMAND    = 11
OFFSET_ACTION = 0   # INT - 0=home, 1=retrieve, 2=store
OFFSET_LEVEL  = 2   # INT - 1=A, 2=B, 3=C
OFFSET_ROW    = 4   # INT - 1, 2, 3
OFFSET_COL    = 6   # INT - 1, 2, 3

# DB12 — Status (we read FROM this)
DB_STATUS         = 12
OFFSET_GRIPPER    = 0  # INT - 0=idle, 1=moving, 2=done, 3=error
OFFSET_CURR_LEVEL = 2  # INT - current level
OFFSET_CURR_ROW   = 4  # INT - current row
OFFSET_CURR_COL   = 6  # INT - current col

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
POLL_INTERVAL     = 0.5   # seconds between checking DB12
COMMAND_TIMEOUT   = 30    # seconds before command times out
LOOP_INTERVAL     = 1     # seconds between middleware loops