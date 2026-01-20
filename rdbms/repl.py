import sys
import os
import json

try:
    from rdbms.database import Database
    from rdbms.ledger import ledger_db
except ImportError:
    from .database import Database
    from .ledger import ledger_db

class REPL:
    def __init__(self):
        self.db = Database()
        self.running = True
        
    def show_help(self):
        help_text = """
        Available Commands:
        
        SQL COMMANDS:
          CREATE TABLE <name> (col1 TYPE, col2 TYPE, ...)
          INSERT INTO <table> VALUES (val1, val2, ...)
          SELECT * FROM <table> [WHERE condition]
          UPDATE <table> SET col=value [WHERE condition]
          DELETE FROM <table> [WHERE condition]
          DROP TABLE <table>
          SHOW TABLES
          
        LEDGER COMMANDS:
          LEDGER CREATE <table_name>           - Create immutable ledger table
          LEDGER APPEND <table> TYPE='type'    - Append event to ledger
                    DATA='{"json":"data"}' 
                    [AGGREGATE='id']
          LEDGER VERIFY <table>                - Verify ledger integrity
          LEDGER AUDIT <table> [AGGREGATE='id'] - Audit events
          
        SYSTEM COMMANDS:
          .tables      - List all tables
          .ledgers     - List all ledger tables
          .exit/.quit  - Exit REPL
          .help/?      - Show this help
        """
        print(help_text)
    
    def handle_command(self, command):
        # Handle system commands first
        if command.lower() in ['.exit', '.quit', 'exit', 'quit']:
            self.running = False
            print("Goodbye!")
            return
        
        elif command.lower() in ['.help', 'help', '?']:
            self.show_help()
            return
        
        elif command == '.tables':
            tables = self.db.list_tables()
            if tables:
                print("Tables in database:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("No tables in database.")
            return
        
        elif command == '.ledgers':
            tables = ledger_db.list_tables()
            if tables:
                print("Ledger Tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("No ledger tables exist.")
            return
        
        # Execute the command
        try:
            # Parse the command first
            parsed = self.db.parser.parse(command)
            
            if not parsed:
                print(f"*** Unknown syntax: {command}")
                return
            
            # Handle SHOW TABLES and ledger commands separately
            if parsed.get('type') == 'SHOW_TABLES':
                self._handle_show_tables()
                return
            elif parsed.get('type', '').startswith('LEDGER_'):
                self._handle_ledger_command(parsed)
                return
            else:
                # Handle regular SQL commands
                result = self.db.execute(command)
                self._handle_sql_result(result)
                
        except Exception as e:
            print(f"Error: {e}")
    
    def _handle_show_tables(self):
        """Handle SHOW TABLES command"""
        tables = self.db.list_tables()
        if tables:
            print("Tables in database:")
            for table in tables:
                print(f"  - {table}")
        else:
            print("No tables in database.")
    
    def _handle_ledger_command(self, parsed):
        """Handle ledger-specific commands"""
        cmd_type = parsed.get('type')
        
        if cmd_type == 'LEDGER_CREATE':
            table_name = parsed['table']
            try:
                table = ledger_db.create_table(table_name)
                print(f"✓ Ledger table '{table_name}' created successfully")
            except ValueError as e:
                print(f"Error: {e}")
                
        elif cmd_type == 'LEDGER_APPEND':
            table_name = parsed['table']
            params = parsed.get('params', {})
            
            table = ledger_db.get_table(table_name)
            if not table:
                print(f"Error: Ledger table '{table_name}' not found")
                return
            
            # Parse JSON data
            try:
                data = json.loads(params.get('data', '{}'))
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON data: {params.get('data')}")
                return
            
            event_id, event_hash = table.append_event(
                event_type=params.get('type', 'EVENT'),
                data=data,
                aggregate_id=params.get('aggregate')
            )
            
            print(f"✓ Event appended. ID: {event_id}, Hash: {event_hash[:16]}...")
            
        elif cmd_type == 'LEDGER_VERIFY':
            table_name = parsed['table']
            table = ledger_db.get_table(table_name)
            if not table:
                print(f"Error: Ledger table '{table_name}' not found")
                return
            
            result = table.verify_chain()
            if result['valid']:
                print(f"✓ Ledger chain valid for '{table_name}' ({result['total_events']} events)")
            else:
                print(f"✗ Ledger chain INVALID for '{table_name}'. {len(result['invalid_events'])} corrupt events")
                
        elif cmd_type == 'LEDGER_AUDIT':
            table_name = parsed['table']
            params = parsed.get('params', {})
            
            table = ledger_db.get_table(table_name)
            if not table:
                print(f"Error: Ledger table '{table_name}' not found")
                return
            
            aggregate_id = params.get('aggregate')
            events = table.get_events(aggregate_id)
            
            if aggregate_id:
                print(f"Audit for '{aggregate_id}' in table '{table_name}':")
            else:
                print(f"Audit for table '{table_name}':")
            
            if not events:
                print("  No events found")
            else:
                for event in events[-10:]:  # Show last 10 events
                    print(f"  [{event['id']}] {event['event_type']}: {event['data']}")
    
    def _handle_sql_result(self, result):
        """Handle SQL command results"""
        if result['status'] == 'success':
            if result['data'] is not None:
                if isinstance(result['data'], list):
                    print(f"Rows: {result['count']}")
                    for row in result['data']:
                        print(f"  {row}")
                else:
                    print(result['message'])
            else:
                print(result['message'])
        elif result['status'] == 'error':
            print(f"Error: {result['message']}")
    
    def run(self):
        print("Welcome to SimpleRDBMS REPL. Type 'help' or '?' for commands.")
        
        while self.running:
            try:
                user_input = input("rdbms> ").strip()
                
                if not user_input:
                    continue
                
                self.handle_command(user_input)
                
            except KeyboardInterrupt:
                print("\nUse '.exit' or '.quit' to exit")
                self.running = False
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")

def main():
    repl = REPL()
    repl.run()

if __name__ == "__main__":
    # This prevents the warning when running as module
    if __package__ is None:
        # Running as script
        main()
    else:
        # Running as module
        main()