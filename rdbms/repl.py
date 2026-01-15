"""
Interactive REPL for the RDBMS
"""
import cmd
from .database import Database
from typing import Dict, List, Any 

class RDBMS_REPL(cmd.Cmd):
    """Interactive SQL REPL"""
    
    intro = "Welcome to SimpleRDBMS REPL. Type 'help' or '?' for commands."
    prompt = "rdbms> "
    
    def __init__(self):
        super().__init__()
        self.db = Database("repl_db")
    
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
    repl = RDBMS_REPL()
    repl.cmdloop()

if __name__ == "__main__":
    main()