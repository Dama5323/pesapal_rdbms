from django.db import models
import uuid
from django.core.validators import MinValueValidator
from users.models import User, Account


try:
    from .audit_mixins import AuditableModel, LedgerTrackedModel
except (ImportError, SyntaxError):
    
    class AuditableModel(models.Model):
        class Meta:
            abstract = True
        def log_change(self, *args, **kwargs):
            pass
    
    class LedgerTrackedModel(models.Model):
        ledger_event_id = models.CharField(max_length=100, blank=True, null=True)
        ledger_hash = models.CharField(max_length=64, blank=True, null=True)
        class Meta:
            abstract = True

# Import rdbms_service directly
try:
    from services import rdbms_service
except ImportError:
    rdbms_service = None

class Transaction(LedgerTrackedModel, AuditableModel):
    """
    Core financial transaction model for PesaPal
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Transaction identifiers
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Public transaction ID shown to users"
    )
    
    internal_reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="Internal reference for reconciliation"
    )
    
    # Parties involved
    from_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='sent_transactions'
    )
    
    to_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='received_transactions'
    )
    
    # Transaction details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    
    currency = models.CharField(
        max_length=3,
        default='KES'
    )
    
    # Transaction type
    TRANSACTION_TYPES = [
        ('TRANSFER', 'Peer to Peer Transfer'),
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('PAYMENT', 'Payment to Merchant'),
        ('BILL_PAYMENT', 'Bill Payment'),
        ('AIRTIME', 'Airtime Purchase'),
        ('INTEREST', 'Interest Payment'),
        ('FEE', 'Service Fee'),
        ('REFUND', 'Refund'),
        ('REVERSAL', 'Transaction Reversal'),
    ]
    transaction_type = models.CharField(
        max_length=50,
        choices=TRANSACTION_TYPES,
        default='TRANSFER'
    )
    
    # Status tracking
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REVERSED', 'Reversed'),
        ('HOLD', 'On Hold'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Financial tracking
    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    net_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Amount after fees and taxes"
    )
    
    # Metadata
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Internal notes")
    
    # Payment method
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('MOBILE_MONEY', 'Mobile Money'),
            ('CARD', 'Credit/Debit Card'),
            ('WALLET', 'Digital Wallet'),
            ('CASH', 'Cash'),
        ],
        default='MOBILE_MONEY'
    )
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='initiated_transactions'
    )
    
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_transactions'
    )
    
    # Reconciliation
    reconciled = models.BooleanField(default=False)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciliation_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-initiated_at']
    
    def __str__(self):
        return f"{self.transaction_id}: {self.amount} {self.currency} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save to record to ledger when completed"""
        is_new = self._state.adding
        
        super().save(*args, **kwargs)
        
        # Log the change
        self.log_change('CREATE' if is_new else 'UPDATE', user=self.initiated_by)
        
        # Record to ledger if completed
        if self.status == 'COMPLETED' and not self.ledger_event_id:
            self.record_to_ledger(user=self.initiated_by)
    
    def to_ledger_format(self):
        """Convert transaction to ledger format"""
        return {
            'id': str(self.id),
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'from_account': str(self.from_account.account_number),
            'to_account': str(self.to_account.account_number),
            'status': self.status,
            'transaction_type': self.transaction_type,
            'description': self.description,
            'metadata': {
                'fee_amount': float(self.fee_amount),
                'tax_amount': float(self.tax_amount),
                'net_amount': float(self.net_amount),
                'payment_method': self.payment_method
            }
        }

# Keep other models simple for now
class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=100, unique=True)
    merchant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    status = models.CharField(max_length=20, default='DRAFT')
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50)
    changes = models.JSONField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.action} on {self.model_name}"
    
