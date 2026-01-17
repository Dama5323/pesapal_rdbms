import os
import sys
from typing import Dict, List, Any, Optional

# Add the rdbms module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rdbms import Database

class RDBMSService:
    """Service layer to connect Django with custom RDBMS"""
    
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RDBMSService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the database connection"""
        # Use a dedicated database for web app
        self._db = Database('pesapal_web')
        
        # Ensure tables exist
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure required tables exist"""
        # Users table
        if 'users' not in self._db.tables:
            self._db.create_table('users', {
                'id': 'INTEGER',
                'username': 'TEXT',
                'email': 'TEXT',
                'first_name': 'TEXT',
                'last_name': 'TEXT',
                'is_active': 'BOOLEAN',
                'date_joined': 'TEXT',
                'last_login': 'TEXT'
            }, primary_key='id', unique_keys=['username', 'email'])
        
        # Tasks table (for JOIN demonstration)
        if 'tasks' not in self._db.tables:
            self._db.create_table('tasks', {
                'id': 'INTEGER',
                'user_id': 'INTEGER',
                'title': 'TEXT',
                'description': 'TEXT',
                'status': 'TEXT',
                'priority': 'TEXT',
                'created_at': 'TEXT',
                'updated_at': 'TEXT',
                'due_date': 'TEXT'
            }, primary_key='id')
    
    # === User Operations ===
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        return self._db.select('users', {})
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        results = self._db.select('users', {'id': user_id})
        return results[0] if results else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        results = self._db.select('users', {'username': username})
        return results[0] if results else None
    
    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user"""
        # Generate ID if not provided
        if 'id' not in user_data:
            # Simple ID generation - get max ID + 1
            all_users = self.get_all_users()
            max_id = max([u.get('id', 0) for u in all_users]) if all_users else 0
            user_data['id'] = max_id + 1
        
        # Set defaults
        if 'is_active' not in user_data:
            user_data['is_active'] = True
        
        self._db.insert('users', user_data)
        return user_data
    
    def update_user(self, user_id: int, updates: Dict) -> bool:
        """Update user"""
        count = self._db.update('users', updates, {'id': user_id})
        return count > 0
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        count = self._db.delete('users', {'id': user_id})
        return count > 0
    
    # === Task Operations ===
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks with user information (JOIN)"""
        # Use JOIN to get user info
        return self._db.join_tables('tasks', 'users', 'user_id', 'id', 'INNER')
    
    def get_tasks_by_user(self, user_id: int) -> List[Dict]:
        """Get tasks for a specific user"""
        return self._db.select('tasks', {'user_id': user_id})
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get task by ID"""
        results = self._db.select('tasks', {'id': task_id})
        return results[0] if results else None
    
    def create_task(self, task_data: Dict) -> Dict:
        """Create a new task"""
        if 'id' not in task_data:
            all_tasks = self._db.select('tasks', {})
            max_id = max([t.get('id', 0) for t in all_tasks]) if all_tasks else 0
            task_data['id'] = max_id + 1
        
        self._db.insert('tasks', task_data)
        return task_data
    
    def update_task(self, task_id: int, updates: Dict) -> bool:
        """Update task"""
        count = self._db.update('tasks', updates, {'id': task_id})
        return count > 0
    
    def delete_task(self, task_id: int) -> bool:
        """Delete task"""
        count = self._db.delete('tasks', {'id': task_id})
        return count > 0
    
    # === SQL Execution ===
    
    def execute_sql(self, sql: str) -> Dict:
        """Execute raw SQL (for SQL executor page)"""
        return self._db.execute(sql)
    
    # === Utility Methods ===
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """Get table structure information"""
        table = self._db.get_table(table_name)
        if table:
            return table.describe()
        return None
    
    def list_tables(self) -> List[str]:
        """List all tables"""
        return self._db.list_tables()
    
    def save_database(self):
        """Persist database to disk"""
        self._db.save()

# Singleton instance
rdbms_service = RDBMSService()