# test_repl_display.py
from rdbms import Database

db = Database('default')

print("=== What Database.execute() returns ===")
result = db.execute("SELECT * FROM users WHERE id = 1")
print(f"Result: {result}")
print(f"Status: {result.get('status')}")
print(f"Message: {result.get('message')}")
print(f"Has data: {'data' in result}")
print(f"Data: {result.get('data')}")
print(f"Data is empty: {not result.get('data')}")