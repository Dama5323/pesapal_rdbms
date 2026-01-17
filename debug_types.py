# debug_types.py
from rdbms.table import Table

# Create test table
table = Table('test', {'id': 'INTEGER', 'name': 'TEXT'}, 'id')

# Insert data
table.insert({'id': 1, 'name': 'John'})
table.insert({'id': 2, 'name': 'Jane'})

print("=== Testing _cast_value method ===")
print(f"_cast_value('id', '1'): {table._cast_value('id', '1')}")
print(f"_cast_value('id', 1): {table._cast_value('id', 1)}")
print(f"Type of _cast_value('id', '1'): {type(table._cast_value('id', '1'))}")

print("\n=== Testing data in table ===")
for i, row in enumerate(table.data):
    print(f"Row {i}: {row}")
    print(f"  id value: {row['id']}, type: {type(row['id'])}")

print("\n=== Testing WHERE conditions ===")
# Test with integer
print(f"WHERE id = 1: {table.select({'id': 1})}")
# Test with string
print(f"WHERE id = '1': {table.select({'id': '1'})}")

print("\n=== Debugging _matches_conditions ===")
# Manually test the comparison
row = table.data[0]
print(f"Row id: {row['id']}, type: {type(row['id'])}")
print(f"Casted '1': {table._cast_value('id', '1')}, type: {type(table._cast_value('id', '1'))}")
print(f"row['id'] == table._cast_value('id', '1'): {row['id'] == table._cast_value('id', '1')}")