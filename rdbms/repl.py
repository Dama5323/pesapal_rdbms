"""
Interactive REPL for the RDBMS
"""
import cmd
from .database import Database
from .parser import SQLParser
from typing import Dict, List, Any 

class REPL(cmd.Cmd):
    """Interactive SQL REPL"""
    
    intro = "Welcome to SimpleRDBMS REPL. Type 'help' or '?' for commands."
    prompt = "rdbms> "
    
    
    def __init__(self):
        super().__init__()
        self.db = Database("repl_db")
        self._initialize_demo_data()  
    
    def _initialize_demo_data(self):
        """Initialize the REPL with demo tables and data"""
        # Only create if they don't exist
        if 'users' not in self.db.tables:
            print("Initializing demo database...")
            
            # Create users table
            self.db.create_table('users', {
                'id': 'INTEGER',
                'name': 'TEXT',
                'email': 'TEXT',
                'role': 'TEXT'
            }, primary_key='id', unique_keys=['email'])
            
            # Create tasks table
            self.db.create_table('tasks', {
                'id': 'INTEGER',
                'user_id': 'INTEGER',
                'title': 'TEXT',
                'description': 'TEXT',
                'status': 'TEXT',
                'priority': 'TEXT'
            }, primary_key='id')
            
            # Insert sample data
            self.db.insert('users', {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'role': 'admin'})
            self.db.insert('users', {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'role': 'user'})
            
            self.db.insert('tasks', {'id': 1, 'user_id': 1, 'title': 'Design database', 'description': 'Create ERD', 'status': 'completed', 'priority': 'high'})
            self.db.insert('tasks', {'id': 2, 'user_id': 2, 'title': 'Write tests', 'description': 'Unit tests', 'status': 'pending', 'priority': 'medium'})
            
            self.db.save()
            print("Demo database ready!")
        
    def do_exec(self, arg):
        """Execute SQL command: exec <sql>"""
        if not arg:
            print("Usage: exec <sql_command>")
            return
        
        result = self.db.execute(arg)
        self._print_result(result)
    
    def do_select(self, arg):
        """Execute SELECT: select <sql_select>"""
        if not arg:
            print("Usage: select <sql_select_statement>")
            return
        
        result = self.db.execute(f"SELECT {arg}")
        self._print_result(result)
    
    def do_insert(self, arg):
        """Execute INSERT: insert <sql_insert>"""
        if not arg:
            print("Usage: insert <sql_insert_statement>")
            return
        
        result = self.db.execute(f"INSERT INTO {arg}")
        self._print_result(result)
    
    def do_tables(self, arg):
        """List all tables"""
        tables = self.db.list_tables()
        if tables:
            print("Tables:")
            for table in tables:
                print(f"  {table}")
        else:
            print("No tables in database")
    
    def do_describe(self, arg):
        """Describe table structure: describe <table_name>"""
        if not arg:
            print("Usage: describe <table_name>")
            return
        
        table = self.db.get_table(arg)
        if not table:
            print(f"Table '{arg}' not found")
            return
        
        desc = table.describe()
        print(f"Table: {desc['name']}")
        print(f"Rows: {desc['row_count']}")
        print(f"Primary Key: {desc['primary_key']}")
        print(f"Unique Keys: {desc['unique_keys']}")
        print("\nColumns:")
        for col, typ in desc['columns'].items():
            print(f"  {col}: {typ}")
    
    def do_save(self, arg):
        """Save database to disk"""
        self.db.save()
        print("Database saved")
    
    def do_exit(self, arg):
        """Exit the REPL"""
        print("Goodbye!")
        return True
    
    def _print_result(self, result: Dict):
        """Print query result"""
        if "error" in result:
            print(f"Error: {result['error']}")
        elif "data" in result:
            data = result["data"]
            if not data:
                print("No rows returned")
                return
            
            # Print as table
            headers = list(data[0].keys())
            print(" | ".join(headers))
            print("-" * (sum(len(str(h)) for h in headers) + 3 * len(headers)))
            
            for row in data:
                values = [str(row.get(h, "")) for h in headers]
                print(" | ".join(values))
            
            print(f"\n{len(data)} row(s) returned")
        else:
            print(result.get("message", "Command executed"))

def main():
    repl = REPL()
    repl.cmdloop()

if __name__ == "__main__":
    main()
