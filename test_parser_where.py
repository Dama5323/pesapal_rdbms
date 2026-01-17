# test_parser_where.py
from rdbms.parser import SQLParser

parser = SQLParser()

test_queries = [
    "SELECT * FROM users WHERE id = 1",
    "SELECT * FROM users WHERE id = '1'",
    "SELECT * FROM users WHERE email = 'john@example.com'",
    "SELECT name FROM users WHERE id = 1"
]

print("=== Testing Parser ===")
for sql in test_queries:
    print(f"\nSQL: {sql}")
    result = parser.parse(sql)
    print(f"  Type: {result.get('type')}")
    print(f"  Table: {result.get('table_name')}")
    print(f"  Conditions: {result.get('conditions')}")
    if result.get('conditions'):
        for col, val in result['conditions'].items():
            print(f"    {col}: {val} (type: {type(val)})")