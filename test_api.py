import requests

BASE = 'http://localhost:5000'

# Test retrieve command
print("Testing retrieve command...")
response = requests.post(f'{BASE}/api/commands/retrieve', json={
    'level': 'C',
    'row'  : 1,
    'col'  : 1
})
print(response.json())

# Test store command
print("\nTesting store command...")
response = requests.post(f'{BASE}/api/commands/store', json={
    'level'    : 'A',
    'row'      : 1,
    'col'      : 1,
    'item_name': 'Test Item'
})
print(response.json())