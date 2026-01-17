# debug_full_flow.py
from rdbms import Database
from rdbms.parser import SQLParser

# Test 1: Direct table access
print("=== Test 1: Direct Table Access ===")
db = Database('test_flow')
if 'users' in db.tables:
    db.drop_table('users')

db.create_table('users', {'id': 'INTEGER', 'name': 'TEXT'}, 'id')
db.insert('users', {'id': 1, 'name': 'John'})

users_table = db.get_table('users')
print(f"Table data: {users_table.data}")

# Direct select
print(f"\nDirect select with {{'id': '1'}}: {users_table.select({'id': '1'})}")
print(f"Direct select with {{'id': 1}}: {users_table.select({'id': 1})}")

# Test 2: Database.execute()
print("\n=== Test 2: Database.execute() ===")
result = db.execute("SELECT * FROM users WHERE id = 1")
print(f"Execute result: {result}")

# Test 3: Check parser output
print("\n=== Test 3: Parser Output ===")
parser = SQLParser()
parsed = parser.parse("SELECT * FROM users WHERE id = 1")
print(f"Parsed: {parsed}")
print(f"Conditions: {parsed.get('conditions')}")

# Test 4: Check Database.select() method
print("\n=== Test 4: Database.select() method ===")
print(f"db.select('users', {{'id': '1'}}): {db.select('users', {'id': '1'})}")
print(f"db.select('users', {{'id': 1}}): {db.select('users', {'id': 1})}")