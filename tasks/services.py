# web/tasks/services.py
"""
Service layer to interact with our custom RDBMS
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../rdbms'))

from rdbms.database import Database


class RDBMSService:
    """Wrapper service for our custom RDBMS"""
    
    def __init__(self):
        self.db = Database("task_manager")
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize database tables if they don't exist"""
        if not self.db.get_table("users"):
            self.db.create_table(
                name="users",
                columns={
                    "id": "INTEGER",
                    "username": "TEXT",
                    "email": "TEXT",
                    "created_at": "DATETIME"
                },
                primary_key="id",
                unique_keys=["email"]
            )
        
        if not self.db.get_table("tasks"):
            self.db.create_table(
                name="tasks",
                columns={
                    "id": "INTEGER",
                    "title": "TEXT",
                    "description": "TEXT",
                    "user_id": "INTEGER",
                    "status": "TEXT",
                    "created_at": "DATETIME",
                    "completed_at": "DATETIME"
                },
                primary_key="id"
            )
        
        # Add sample data
        if self.db.get_table("users").count() == 0:
            sample_users = [
                {"id": 1, "username": "admin", "email": "admin@example.com", "created_at": "2024-01-01"},
                {"id": 2, "username": "john", "email": "john@example.com", "created_at": "2024-01-02"},
                {"id": 3, "username": "jane", "email": "jane@example.com", "created_at": "2024-01-03"}
            ]
            for user in sample_users:
                self.db.get_table("users").insert(user)
        
        if self.db.get_table("tasks").count() == 0:
            sample_tasks = [
                {"id": 1, "title": "Setup project", "description": "Initialize the project", "user_id": 1, "status": "completed"},
                {"id": 2, "title": "Build RDBMS", "description": "Create database engine", "user_id": 1, "status": "in-progress"},
                {"id": 3, "title": "Create web interface", "description": "Build Django app", "user_id": 2, "status": "pending"}
            ]
            for task in sample_tasks:
                self.db.get_table("tasks").insert(task)
    
    def get_all_users(self):
        """Get all users"""
        return self.db.get_table("users").select()
    
    def get_user(self, user_id):
        """Get user by ID"""
        users = self.db.get_table("users").select({"id": user_id})
        return users[0] if users else None
    
    def create_user(self, user_data):
        """Create new user"""
        # Generate ID
        all_users = self.db.get_table("users").select()
        new_id = max([u.get("id", 0) for u in all_users]) + 1 if all_users else 1
        user_data["id"] = new_id
        
        self.db.get_table("users").insert(user_data)
        return user_data
    
    def update_user(self, user_id, user_data):
        """Update user"""
        user_data["id"] = user_id
        count = self.db.get_table("users").update(user_data, {"id": user_id})
        return count > 0
    
    def delete_user(self, user_id):
        """Delete user"""
        count = self.db.get_table("users").delete({"id": user_id})
        return count > 0
    
    def get_all_tasks(self):
        """Get all tasks with user info (JOIN)"""
        users_table = self.db.get_table("users")
        tasks_table = self.db.get_table("tasks")
        
        # Perform JOIN
        joined_data = tasks_table.join(users_table, "user_id", "id", "LEFT")
        
        # Format results
        results = []
        for row in joined_data:
            results.append({
                "id": row.get("id"),
                "title": row.get("title"),
                "description": row.get("description"),
                "status": row.get("status"),
                "user": {
                    "id": row.get("user_id"),
                    "username": row.get("username"),
                    "email": row.get("email")
                }
            })
        
        return results
    
    def get_user_tasks(self, user_id):
        """Get tasks for a specific user"""
        tasks = self.db.get_table("tasks").select({"user_id": user_id})
        user = self.get_user(user_id)
        
        for task in tasks:
            task["user"] = user
        
        return tasks
    
    def create_task(self, task_data):
        """Create new task"""
        all_tasks = self.db.get_table("tasks").select()
        new_id = max([t.get("id", 0) for t in all_tasks]) + 1 if all_tasks else 1
        task_data["id"] = new_id
        
        self.db.get_table("tasks").insert(task_data)
        return task_data
    
    def update_task(self, task_id, task_data):
        """Update task"""
        task_data["id"] = task_id
        count = self.db.get_table("tasks").update(task_data, {"id": task_id})
        return count > 0
    
    def delete_task(self, task_id):
        """Delete task"""
        count = self.db.get_table("tasks").delete({"id": task_id})
        return count > 0
    
    def execute_sql(self, sql):
        """Execute raw SQL"""
        return self.db.execute(sql)

# Singleton instance
rdbms_service = RDBMSService()