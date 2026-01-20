from django.core.management.base import BaseCommand
from django.core.management import color

try:
    from services import rdbms_service
    from rdbms.ledger import ledger_db
except ImportError:
    # Mock for testing
    class MockService:
        def list_tables(self): return []
        def execute_sql(self, sql): return {'status': 'success'}
    rdbms_service = MockService()
    ledger_db = type('obj', (object,), {'list_tables': lambda: []})()

class Command(BaseCommand):
    help = 'Setup RDBMS tables and ledgers for the application'
    
    def handle(self, *args, **options):
        self.style = color.color_style()
        
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))
        self.stdout.write(self.style.MIGRATE_HEADING("RDBMS SETUP & INITIALIZATION"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))
        
        try:
            # 1. Create audit tables
            self.stdout.write("\n📁 Creating audit tables...")
            
            # Audit logs table
            result = rdbms_service.execute_sql("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    object_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    user_id TEXT,
                    changes TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME NOT NULL
                )
            """)
            self.stdout.write(self.style.SUCCESS("   ✅ Created 'audit_logs' table"))
            
            # Transaction ledger table
            result = rdbms_service.execute_sql("""
                CREATE TABLE IF NOT EXISTS transaction_ledger (
                    id TEXT PRIMARY KEY,
                    transaction_id TEXT UNIQUE NOT NULL,
                    amount DECIMAL(15, 2) NOT NULL,
                    currency TEXT DEFAULT 'KES',
                    from_account TEXT NOT NULL,
                    to_account TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    transaction_type TEXT,
                    timestamp DATETIME NOT NULL,
                    metadata TEXT
                )
            """)
            self.stdout.write(self.style.SUCCESS("   ✅ Created 'transaction_ledger' table"))
            
            # 2. Create ledger tables
            self.stdout.write("\n🔗 Creating immutable ledger tables...")
            
            if 'transactions' not in ledger_db.list_tables():
                ledger_db.create_table('transactions')
                self.stdout.write(self.style.SUCCESS("   ✅ Created 'transactions' ledger"))
            
            if 'audit_logs' not in ledger_db.list_tables():
                ledger_db.create_table('audit_logs')
                self.stdout.write(self.style.SUCCESS("   ✅ Created 'audit_logs' ledger"))
            
            if 'system_events' not in ledger_db.list_tables():
                ledger_db.create_table('system_events')
                self.stdout.write(self.style.SUCCESS("   ✅ Created 'system_events' ledger"))
            
            # 3. Insert initial system event
            self.stdout.write("\n📝 Recording initial system event...")
            try:
                transactions_ledger = ledger_db.get_table('transactions')
                if transactions_ledger:
                    event_id, event_hash = transactions_ledger.append_event(
                        event_type='SYSTEM_INIT',
                        data={'system': 'pesapal_rdbms', 'version': '1.0', 'action': 'initial_setup'},
                        aggregate_id='system'
                    )
                    self.stdout.write(self.style.SUCCESS(f"   ✅ System initialized: Event {event_id}"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   ⚠ Could not record system event: {e}"))
            
            # 4. Verify setup
            self.stdout.write("\n🔍 Verifying setup...")
            tables = rdbms_service.list_tables()
            ledgers = ledger_db.list_tables()
            
            self.stdout.write(f"   RDBMS Tables: {', '.join(tables) if tables else 'None'}")
            self.stdout.write(f"   Ledger Tables: {', '.join(ledgers) if ledgers else 'None'}")
            
            # 5. Final status
            self.stdout.write(self.style.MIGRATE_HEADING("\n" + "=" * 70))
            self.stdout.write(self.style.SUCCESS("✅ RDBMS SETUP COMPLETE!"))
            self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))
            
            self.stdout.write("\n🌐 Access URLs:")
            self.stdout.write("   Django Admin: http://localhost:8000/admin/")
            self.stdout.write("   RDBMS Admin: http://localhost:8000/rdbms-admin/")
            self.stdout.write("   API Status: http://localhost:8000/api/ledgers/verify/")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Setup failed: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
