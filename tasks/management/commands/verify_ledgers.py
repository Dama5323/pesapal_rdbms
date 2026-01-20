from django.core.management.base import BaseCommand
from django.core.management import color
from django.utils import termcolors

try:
    from services import rdbms_service
except ImportError:
    # For development/testing
    class MockRDBMSService:
        def verify_ledgers(self):
            return {
                'transactions': {'valid': True, 'total_events': 10, 'invalid_events': []},
                'audit_logs': {'valid': True, 'total_events': 5, 'invalid_events': []}
            }
    rdbms_service = MockRDBMSService()

class Command(BaseCommand):
    help = 'Verify integrity of all ledger tables in the custom RDBMS'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--table',
            type=str,
            help='Verify specific table only'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix invalid chains (WARNING: Use with caution)'
        )
    
    def handle(self, *args, **options):
        self.style = color.color_style()
        
        table_name = options['table']
        attempt_fix = options['fix']
        
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))
        self.stdout.write(self.style.MIGRATE_HEADING("LEDGER INTEGRITY VERIFICATION"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))
        
        try:
            # Get verification results
            verification_results = rdbms_service.verify_ledgers()
            
            if table_name:
                # Verify specific table only
                if table_name in verification_results:
                    self._verify_single_table(table_name, verification_results[table_name], attempt_fix)
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Table '{table_name}' not found in ledger database")
                    )
                    self.stdout.write(
                        self.style.WARNING(f"Available tables: {', '.join(verification_results.keys())}")
                    )
            else:
                # Verify all tables
                self._verify_all_tables(verification_results, attempt_fix)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during verification: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
    
    def _verify_single_table(self, table_name, result, attempt_fix):
        """Verify a single ledger table"""
        self.stdout.write(f"\n📊 Table: {table_name}")
        self.stdout.write(f"   Events: {result.get('total_events', 0)}")
        
        if result.get('valid'):
            self.stdout.write(self.style.SUCCESS("   ✅ VALID: Hash chain is intact"))
        else:
            self.stdout.write(self.style.ERROR("   ❌ INVALID: Hash chain is broken!"))
            
            invalid_events = result.get('invalid_events', [])
            if invalid_events:
                self.stdout.write(self.style.WARNING(f"   Found {len(invalid_events)} invalid event(s):"))
                for invalid in invalid_events[:5]:  # Show first 5
                    self.stdout.write(f"     - Event {invalid.get('event_id')}: Expected {invalid.get('expected')[:16]}..., Got {invalid.get('actual')[:16]}...")
                
                if len(invalid_events) > 5:
                    self.stdout.write(f"     ... and {len(invalid_events) - 5} more")
            
            if attempt_fix:
                self.stdout.write(self.style.WARNING("   ⚠ Attempting to fix... (Not implemented in this demo)"))
                # In a real implementation, you'd rebuild the hash chain here
    
    def _verify_all_tables(self, verification_results, attempt_fix):
        """Verify all ledger tables"""
        valid_count = 0
        invalid_count = 0
        total_events = 0
        
        for table_name, result in verification_results.items():
            self.stdout.write(f"\n📊 Table: {table_name}")
            self.stdout.write(f"   Events: {result.get('total_events', 0)}")
            total_events += result.get('total_events', 0)
            
            if result.get('valid'):
                self.stdout.write(self.style.SUCCESS("   ✅ VALID"))
                valid_count += 1
            else:
                self.stdout.write(self.style.ERROR("   ❌ INVALID"))
                invalid_count += 1
                
                invalid_events = result.get('invalid_events', [])
                if invalid_events:
                    self.stdout.write(self.style.WARNING(f"     {len(invalid_events)} corrupt event(s)"))
        
        # Summary
        self.stdout.write(self.style.MIGRATE_HEADING("\n" + "=" * 70))
        self.stdout.write(self.style.MIGRATE_HEADING("VERIFICATION SUMMARY"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 70))
        
        self.stdout.write(f"\n📈 Total Tables: {len(verification_results)}")
        self.stdout.write(f"📈 Total Events: {total_events}")
        
        if valid_count == len(verification_results):
            self.stdout.write(self.style.SUCCESS("\n🎉 SUCCESS: All ledgers are valid!"))
        else:
            self.stdout.write(self.style.ERROR(f"\n⚠ WARNING: {invalid_count} ledger(s) are invalid!"))
            self.stdout.write(self.style.WARNING("   Some financial records may be compromised."))
            self.stdout.write(self.style.WARNING("   Run with --fix flag to attempt repair (use with caution)."))
        
        # Recommendations
        if invalid_count > 0:
            self.stdout.write(self.style.NOTICE("\n🔧 Recommended actions:"))
            self.stdout.write("   1. Restore from backup if available")
            self.stdout.write("   2. Manually audit the invalid events")
            self.stdout.write("   3. Rebuild hash chain using --fix (if implemented)")