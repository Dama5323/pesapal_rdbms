from django.db import models

# Try to import RDBMS service
try:
    from services import rdbms_service
    RDBMS_AVAILABLE = True
except ImportError:
    RDBMS_AVAILABLE = False
    rdbms_service = None

class AuditableModel(models.Model):
    """
    Mixin to add audit logging to any Django model
    """
    class Meta:
        abstract = True
    
    def log_change(self, action, user=None, request=None, extra_data=None):
        """
        Log changes to this model instance
        """
        if not RDBMS_AVAILABLE or not rdbms_service:
            return False
        
        try:
            # Get user ID
            user_id = None
            if user:
                if hasattr(user, 'id'):
                    user_id = str(user.id)
                else:
                    user_id = str(user)
            
            # Prepare changes data
            changes = {
                'model': self.__class__.__name__,
                'object_id': str(self.pk),
                'action': action,
            }
            
            if extra_data:
                changes.update(extra_data)
            
            # Get request info if available
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            # Log to custom RDBMS
            return rdbms_service.log_audit(
                model_name=self.__class__.__name__,
                object_id=str(self.pk),
                action=action,
                user_id=user_id or 'system',
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
        except Exception as e:
            print(f"Error logging audit: {e}")
            return False

class LedgerTrackedModel(models.Model):
    """
    Mixin for models that need immutable ledger tracking
    """
    ledger_event_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Immutable ledger event ID"
    )
    
    ledger_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Cryptographic hash from ledger"
    )
    
    class Meta:
        abstract = True
    
    def record_to_ledger(self, user=None, extra_metadata=None):
        """
        Record this instance to immutable ledger
        """
        if not RDBMS_AVAILABLE or not rdbms_service:
            return {'success': False, 'error': 'RDBMS service not available'}
        
        try:
            ledger_data = self.to_ledger_format()
            
            if extra_metadata:
                ledger_data['metadata'].update(extra_metadata)
            
            # Add user info if available
            if user:
                if hasattr(user, 'id'):
                    ledger_data['user_id'] = str(user.id)
                    ledger_data['username'] = user.username
                else:
                    ledger_data['user_id'] = str(user)
            
            # Record to ledger
            result = rdbms_service.record_transaction(ledger_data)
            
            if result.get('success'):
                # Store ledger reference
                self.ledger_event_id = result.get('ledger_event_id')
                self.ledger_hash = result.get('hash')
                
                # Save without triggering infinite loop
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE {} SET ledger_event_id = %s, ledger_hash = %s WHERE id = %s".format(
                            self._meta.db_table
                        ),
                        [self.ledger_event_id, self.ledger_hash, self.pk]
                    )
            
            return result
            
        except Exception as e:
            print(f"Error recording to ledger: {e}")
            return {'success': False, 'error': str(e)}
    
    def to_ledger_format(self):
        """
        Convert model to ledger format - MUST override in subclasses
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement to_ledger_format() method"
        )