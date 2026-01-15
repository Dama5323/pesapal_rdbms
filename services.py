# pesapal_rdbms/services.py  (CREATE THIS IN PROJECT ROOT)
"""
Shared RDBMS service for Django apps
"""
import sys
import os

# Add paths
project_root = os.path.dirname(os.path.abspath(__file__))
rdbms_path = os.path.join(project_root, 'rdbms')

for path in [project_root, rdbms_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

print(f"Project root: {project_root}")
print(f"RDBMS path: {rdbms_path}")

try:
    from rdbms.database import Database
    print("✓ Successfully imported custom RDBMS")
    
    # Create database instance
    db = Database("pesapal_web_db")
    
    # Setup tables if they don't exist
    if not db.get_table("users"):
        db.create_table(
            name="users",
            columns={
                "id": "INTEGER",
                "username": "TEXT",
                "email": "TEXT",
                "full_name": "TEXT",
                "created_at": "DATETIME"
            },
            primary_key="id",
            unique_keys=["email", "username"]
        )
        print("Created users table")
    
    if not db.get_table("tasks"):
        db.create_table(
            name="tasks",
            columns={
                "id": "INTEGER",
                "title": "TEXT",
                "description": "TEXT",
                "user_id": "INTEGER",
                "status": "TEXT",
                "priority": "TEXT",
                "created_at": "DATETIME",
                "due_date": "DATETIME"
            },
            primary_key="id"
        )
        print("Created tasks table")
    
    # Add sample data
    users_table = db.get_table("users")
    if users_table.count() == 0:
        sample_users = [
            {"id": 1, "username": "admin", "email": "admin@pesapal.com", "full_name": "Admin User", "created_at": "2024-01-01"},
            {"id": 2, "username": "john", "email": "john@pesapal.com", "full_name": "John Doe", "created_at": "2024-01-02"},
            {"id": 3, "username": "jane", "email": "jane@pesapal.com", "full_name": "Jane Smith", "created_at": "2024-01-03"},
        ]
        for user in sample_users:
            users_table.insert(user)
        print(f"Added {len(sample_users)} sample users")
    
    tasks_table = db.get_table("tasks")
    if tasks_table.count() == 0:
        sample_tasks = [
            {"id": 1, "title": "Setup RDBMS", "description": "Build custom database engine", "user_id": 1, "status": "completed", "priority": "high", "created_at": "2024-01-10", "due_date": "2024-01-15"},
            {"id": 2, "title": "Create Web API", "description": "Build Django REST API", "user_id": 1, "status": "in_progress", "priority": "high", "created_at": "2024-01-11", "due_date": "2024-01-18"},
            {"id": 3, "title": "Design UI", "description": "Create user interface", "user_id": 2, "status": "pending", "priority": "medium", "created_at": "2024-01-12", "due_date": "2024-01-20"},
        ]
        for task in sample_tasks:
            tasks_table.insert(task)
        print(f"Added {len(sample_tasks)} sample tasks")
    
    rdbms_service = db
    
except ImportError as e:
    print(f"⚠ Could not import RDBMS: {e}")
    print("⚠ Using mock database for development")
    
    # Mock database
    class MockDatabase:
        def __init__(self, name):
            self.name = name
            self.tables = {
                "users": MockTable(),
                "tasks": MockTable()
            }
        
        def get_table(self, name):
            return self.tables.get(name)
        
        def execute(self, sql):
            return {"message": "Mock database", "sql": sql}
    
    class MockTable:
        def __init__(self):
            self.data = []
            self.columns = {}
        
        def insert(self, row):
            self.data.append(row)
            return len(self.data) - 1
        
        def select(self, where=None):
            if not where:
                return self.data
            # Simple filtering
            results = []
            for row in self.data:
                match = True
                for key, value in where.items():
                    if row.get(key) != value:
                        match = False
                        break
                if match:
                    results.append(row)
            return results
        
        def count(self):
            return len(self.data)
        
        def join(self, other, left_on, right_on, join_type="INNER"):
            # Simple mock join
            results = []
            for left in self.data:
                for right in other.data:
                    if left.get(left_on) == right.get(right_on):
                        merged = left.copy()
                        for k, v in right.items():
                            merged[f"{other.name}_{k}"] = v
                        results.append(merged)
            return results
    
    rdbms_service = MockDatabase("mock_db")
    
    # Add mock data
    mock_users = [
        {"id": 1, "username": "admin", "email": "admin@pesapal.com", "full_name": "Admin User", "created_at": "2024-01-01"},
        {"id": 2, "username": "john", "email": "john@pesapal.com", "full_name": "John Doe", "created_at": "2024-01-02"},
    ]
    for user in mock_users:
        rdbms_service.tables["users"].insert(user)
    
    mock_tasks = [
        {"id": 1, "title": "Setup RDBMS", "description": "Build database", "user_id": 1, "status": "completed"},
        {"id": 2, "title": "Create API", "description": "Build REST API", "user_id": 1, "status": "in_progress"},
    ]
    for task in mock_tasks:
        rdbms_service.tables["tasks"].insert(task)

print("✓ RDBMS service initialized")