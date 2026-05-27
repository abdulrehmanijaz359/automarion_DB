import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='automation_db'
)
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO alarms
    (alarm_type, severity, message, resolved)
    VALUES ('Test Gripper Error', 'critical',
    'Gripper failed to reach position A(1,1)', FALSE)
""")
conn.commit()
conn.close()
print("Test alarm created!")
print("Check your web page for the red banner!")