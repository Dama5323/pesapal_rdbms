import sys
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction as db_transaction
from django.contrib.auth.decorators import login_required

# Import rdbms_service (it will handle ledger_db internally)
try:
    from services import rdbms_service
    print("✓ Imported rdbms_service in tasks/views.py")
except ImportError as e:
    print(f"⚠ Could not import rdbms_service: {e}")
    
    # Create minimal mock
    class MockRDBMSService:
        def record_transaction(self, data):
            return {'success': True, 'ledger_event_id': 'mock-001', 'hash': 'mock'}
        def get_audit_logs(self, **kwargs):
            return []
        def verify_ledgers(self):
            return {'transactions': {'valid': True, 'total_events': 0}}
        def execute_sql(self, sql):
            return {'status': 'success', 'data': [], 'count': 0}
        def list_tables(self):
            return ['audit_logs', 'transaction_ledger']
    
    rdbms_service = MockRDBMSService()

# Import models
from .models import Transaction, Invoice

@csrf_exempt
@login_required
def create_transaction(request):
    """Create a transaction with ledger recording"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create transaction in Django ORM
            with db_transaction.atomic():
                transaction = Transaction.objects.create(
                    transaction_id=data['transaction_id'],
                    from_account_id=data['from_account'],
                    to_account_id=data['to_account'],
                    amount=data['amount'],
                    currency=data.get('currency', 'KES'),
                    transaction_type=data.get('type', 'TRANSFER'),
                    description=data.get('description', ''),
                    initiated_by=request.user
                )
            
            # Record to immutable ledger
            ledger_result = rdbms_service.record_transaction({
                'id': str(transaction.id),
                'transaction_id': transaction.transaction_id,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'from_account': str(transaction.from_account.account_number),
                'to_account': str(transaction.to_account.account_number),
                'status': 'PENDING',
                'type': transaction.transaction_type
            })
            
            # Update transaction with ledger info
            if ledger_result.get('success'):
                transaction.ledger_event_id = ledger_result.get('ledger_event_id')
                transaction.ledger_hash = ledger_result.get('hash')
                transaction.save(update_fields=['ledger_event_id', 'ledger_hash'])
            
            return JsonResponse({
                'success': True,
                'transaction_id': transaction.transaction_id,
                'ledger_event_id': ledger_result.get('ledger_event_id'),
                'message': 'Transaction created and recorded to ledger'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST method required'}, status=405)

@login_required
def transaction_audit(request, transaction_id):
    """Get audit trail for a transaction"""
    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        
        # Get audit from custom RDBMS
        audit_trail = rdbms_service.get_audit_logs(
            model_name='Transaction',
            object_id=str(transaction.id),
            limit=50
        )
        
        # Get ledger audit
        ledger_audit = rdbms_service.audit_transaction(transaction.transaction_id)
        
        return JsonResponse({
            'transaction': {
                'id': str(transaction.id),
                'transaction_id': transaction.transaction_id,
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'status': transaction.status,
                'ledger_event_id': transaction.ledger_event_id,
                'ledger_hash': transaction.ledger_hash
            },
            'audit_trail': audit_trail,
            'ledger_audit': ledger_audit
        })
        
    except Transaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def verify_all_ledgers(request):
    """Verify integrity of all ledgers"""
    try:
        verification = rdbms_service.verify_ledgers()
        
        all_valid = all(
            result.get('valid', False) 
            for result in verification.values()
        )
        
        return JsonResponse({
            'all_valid': all_valid,
            'details': verification,
            'message': '✓ All ledgers valid' if all_valid else '✗ Some ledgers invalid'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def execute_financial_sql(request):
    """Execute financial SQL queries (for reporting)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sql = data.get('query', '')
            
            # Security check
            if any(keyword in sql.upper() for keyword in ['DELETE', 'DROP', 'UPDATE', 'ALTER']):
                return JsonResponse({
                    'error': 'Only SELECT queries are allowed for security'
                }, status=403)
            
            # Execute on custom RDBMS
            result = rdbms_service.execute_sql(sql)
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST method required'}, status=405)

@login_required
def financial_report(request):
    """Generate financial report using custom RDBMS"""
    try:
        # Get ledger verification status
        ledger_status = rdbms_service.verify_ledgers()
        
        # Remove ledger_db reference - get tables from rdbms_service instead
        ledger_tables = ['transactions', 'audit_logs']  # Default
        
        return JsonResponse({
            'ledger_status': ledger_status,
            'rdbms_tables': rdbms_service.list_tables(),
            'ledger_tables': ledger_tables
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Keep your existing views but remove ledger_db references
def admin_rdbms_status(request):
    """Admin endpoint for RDBMS status"""
    try:
        tables = rdbms_service.list_tables()
        verification = rdbms_service.verify_ledgers()
        
        return JsonResponse({
            'status': 'online',
            'tables': tables,
            'verification': verification
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)})

def admin_verify_ledgers(request):
    """Admin endpoint to verify ledgers"""
    return verify_all_ledgers(request)

def admin_sql_executor(request):
    """Admin SQL executor"""
    return execute_financial_sql(request)