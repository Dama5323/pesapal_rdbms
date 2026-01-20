# services/rdbms_service.py - CLEAN VERSION
import sys
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Try to import RDBMS modules with multiple fallbacks
Database = None
ledger_db = None

try:
    # Try absolute import first
    from rdbms.database import Database
    from rdbms.ledger import ledger_db
    print("Successfully imported RDBMS modules")
except ImportError:
    try:
        # Try different import style
        import rdbms.database
        import rdbms.ledger
        Database = rdbms.database.Database
        ledger_db = rdbms.ledger.ledger_db
        print("Imported RDBMS modules via import rdbms")
    except ImportError:
        print("RDBMS modules not found. Using mock implementations.")
        
        # Mock Database class
        class MockDatabase:
            def __init__(self, name="mock"):
                self.name = name
                self.tables = {}
            
            def execute(self, sql):
                print(f"[MOCK DB] Executing: {sql[:50]}...")
                return {
                    'status': 'success', 
                    'message': 'Mock execution', 
                    'data': [],
                    'count': 0
                }
            
            def list_tables(self):
                return list(self.tables.keys())
        
        # Mock LedgerDB
        class MockLedgerDB:
            def __init__(self):
                self.tables = {}
            
            def create_table(self, name):
                class MockLedgerTable:
                    def __init__(self):
                        self.events = []
                    
                    def append_event(self, event_type, data, aggregate_id=None):
                        event_id = len(self.events)
                        event_hash = f"mock_hash_{event_id}"
                        self.events.append({
                            'id': event_id,
                            'event_type': event_type,
                            'data': data,
                            'aggregate_id': aggregate_id,
                            'hash': event_hash
                        })
                        return event_id, event_hash
                    
                    def get_events(self, aggregate_id=None):
                        if aggregate_id:
                            return [e for e in self.events if e.get('aggregate_id') == aggregate_id]
                        return self.events
                    
                    def verify_chain(self):
                        return {'valid': True, 'total_events': len(self.events), 'invalid_events': []}
                
                self.tables[name] = MockLedgerTable()
                return self.tables[name]
            
            def get_table(self, name):
                return self.tables.get(name)
            
            def list_tables(self):
                return list(self.tables.keys())
        
        Database = MockDatabase
        ledger_db = MockLedgerDB()

class RDBMSService:
    """Service layer to integrate custom RDBMS with Django"""
    
    def __init__(self):
        if Database:
            self.db = Database("pesapal_audit")
        else:
            self.db = None
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure required tables exist"""
        if not self.db:
            return
        
        # Audit log table
        if 'audit_logs' not in self.db.list_tables():
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    model_name TEXT,
                    object_id TEXT,
                    action TEXT,
                    user_id TEXT,
                    changes TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TEXT
                )
            """)
        
        # Transaction ledger table
        if 'transaction_ledger' not in self.db.list_tables():
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS transaction_ledger (
                    id TEXT PRIMARY KEY,
                    transaction_id TEXT,
                    amount REAL,
                    currency TEXT,
                    from_account TEXT,
                    to_account TEXT,
                    status TEXT,
                    timestamp TEXT,
                    metadata TEXT
                )
            """)
    
    # AUDIT LOGGING
    
    def log_audit(self, model_name: str, object_id: str, action: str, 
                 user_id: str, changes: Dict, ip_address: str = None,
                 user_agent: str = None) -> bool:
        """Log an audit event in the custom RDBMS"""
        try:
            if not self.db:
                print(f"[MOCK] Audit log: {model_name} {action} {object_id}")
                return True
            
            audit_id = str(uuid.uuid4())
            
            self.db.execute(f"""
                INSERT INTO audit_logs 
                (id, model_name, object_id, action, user_id, changes, ip_address, user_agent, timestamp)
                VALUES ('{audit_id}', '{model_name}', '{object_id}', '{action}', 
                        '{user_id}', '{json.dumps(changes)}', '{ip_address or ''}', 
                        '{user_agent or ''}', '{datetime.now().isoformat()}')
            """)
            
            return True
        except Exception as e:
            print(f"Audit logging error: {e}")
            return False
    
    def get_audit_logs(self, model_name: str = None, user_id: str = None, 
                      limit: int = 100) -> List[Dict]:
        """Get audit logs from custom RDBMS"""
        if not self.db:
            return []
        
        query = "SELECT * FROM audit_logs"
        conditions = []
        
        if model_name:
            conditions.append(f"model_name = '{model_name}'")
        if user_id:
            conditions.append(f"user_id = '{user_id}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        result = self.db.execute(query)
        return result.get('data', [])
    
    # TRANSACTION LEDGER
    
    def record_transaction(self, transaction_data: Dict) -> Dict:
        """
        Record a transaction in the immutable ledger
        """
        try:
            tx_id = transaction_data.get('id', str(uuid.uuid4()))
            
            # Record in regular RDBMS table
            if self.db:
                self.db.execute(f"""
                    INSERT INTO transaction_ledger 
                    (id, transaction_id, amount, currency, from_account, to_account, status, timestamp, metadata)
                    VALUES ('{tx_id}', '{transaction_data.get('transaction_id')}', 
                            {transaction_data.get('amount', 0)}, '{transaction_data.get('currency', 'KES')}',
                            '{transaction_data.get('from_account')}', '{transaction_data.get('to_account')}',
                            '{transaction_data.get('status', 'PENDING')}', 
                            '{datetime.now().isoformat()}', 
                            '{json.dumps(transaction_data)}')
                """)
            
            # Record in immutable ledger
            ledger_result = self._ledger_record_transaction(transaction_data)
            
            return {
                'transaction_id': tx_id,
                'ledger_event_id': ledger_result.get('event_id'),
                'hash': ledger_result.get('hash'),
                'success': True
            }
            
        except Exception as e:
            print(f"Transaction recording error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_transaction_history(self, account_id: str = None, 
                               limit: int = 100) -> List[Dict]:
        """Get transaction history from custom RDBMS"""
        if not self.db:
            return []
        
        query = "SELECT * FROM transaction_ledger"
        
        if account_id:
            query += f" WHERE from_account = '{account_id}' OR to_account = '{account_id}'"
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        result = self.db.execute(query)
        return result.get('data', [])
    
    # IMMUTABLE LEDGER METHODS
    
    def _ledger_record_transaction(self, transaction_data: Dict):
        """Record transaction in immutable ledger"""
        if not ledger_db:
            return {'event_id': 'mock-001', 'hash': 'mock_hash'}
        
        if 'transactions' not in ledger_db.list_tables():
            ledger_db.create_table('transactions')
        
        ledger_table = ledger_db.get_table('transactions')
        
        # Create summary event
        summary_event = {
            'transaction_id': transaction_data.get('transaction_id'),
            'amount': float(transaction_data.get('amount', 0)),
            'currency': transaction_data.get('currency', 'KES'),
            'from_account': transaction_data.get('from_account'),
            'to_account': transaction_data.get('to_account'),
            'status': transaction_data.get('status', 'PENDING'),
            'timestamp': datetime.now().isoformat(),
            'metadata': transaction_data
        }
        
        event_id, event_hash = ledger_table.append_event(
            event_type='TRANSACTION_RECORDED',
            data=summary_event,
            aggregate_id=transaction_data.get('transaction_id')
        )
        
        return {
            'event_id': event_id,
            'hash': event_hash
        }
    
    # LEDGER VERIFICATION
    
    def verify_ledgers(self) -> Dict:
        """Verify integrity of all ledger tables"""
        if not ledger_db:
            return {'mock': {'valid': True, 'total_events': 0, 'invalid_events': []}}
        
        results = {}
        
        for table_name in ledger_db.list_tables():
            table = ledger_db.get_table(table_name)
            if table:
                results[table_name] = table.verify_chain()
        
        return results
    
    def audit_transaction(self, transaction_id: str) -> Dict:
        """Get full audit trail for a transaction"""
        if not ledger_db or 'transactions' not in ledger_db.list_tables():
            return {
                'transaction_id': transaction_id,
                'events': [],
                'event_count': 0,
                'note': 'Using mock ledger'
            }
        
        ledger_table = ledger_db.get_table('transactions')
        events = ledger_table.get_events(transaction_id)
        
        return {
            'transaction_id': transaction_id,
            'events': events,
            'event_count': len(events)
        }
    
    # SQL EXECUTOR
    
    def execute_sql(self, sql: str) -> Dict:
        """Execute raw SQL on the custom RDBMS"""
        if not self.db:
            return {
                'status': 'success',
                'message': 'Mock SQL execution',
                'data': [],
                'count': 0
            }
        
        return self.db.execute(sql)
    
    def list_tables(self) -> List[str]:
        """List all tables in custom RDBMS"""
        if not self.db:
            return ['audit_logs', 'transaction_ledger']
        
        return self.db.list_tables()

# Global instance
rdbms_service = RDBMSService()
print(f"RDBMSService initialized. DB: {'Available' if rdbms_service.db else 'Mock'}")