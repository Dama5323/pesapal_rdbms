# tasks/models.py
from django.db import models
import uuid
from django.core.validators import MinValueValidator
from users.models import User, Account

class Transaction(models.Model):
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
    
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=1.000000,
        help_text="Exchange rate if currency conversion occurred"
    )
    
    converted_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount after currency conversion"
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
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['from_account', 'initiated_at']),
            models.Index(fields=['to_account', 'initiated_at']),
            models.Index(fields=['status', 'initiated_at']),
            models.Index(fields=['transaction_type', 'initiated_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name='positive_amount'
            ),
        ]
    
    def __str__(self):
        return f"{self.transaction_id}: {self.amount} {self.currency} ({self.status})"

class Invoice(models.Model):
    """
    Invoice model for merchant payments
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    invoice_number = models.CharField(max_length=100, unique=True)
    
    # Merchant who created the invoice
    merchant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoices',
        limit_choices_to={'is_staff': False}  # Regular merchants, not staff
    )
    
    # Customer details
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Invoice details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    
    # Status
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('VIEWED', 'Viewed'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
        ('PARTIALLY_PAID', 'Partially Paid'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Dates
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    paid_date = models.DateTimeField(null=True, blank=True)
    
    # Payment tracking
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    
    remaining_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    
    # Items
    items = models.JSONField(
        default=list,
        help_text="List of invoice items in JSON format"
    )
    
    # Metadata
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    # Transaction reference (if paid)
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.amount} {self.currency}"

class AuditLog(models.Model):
    """
    Audit log for tracking all financial activities
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # What was changed
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    
    # Who changed it
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Change details
    action = models.CharField(
        max_length=50,
        choices=[
            ('CREATE', 'Create'),
            ('UPDATE', 'Update'),
            ('DELETE', 'Delete'),
            ('VIEW', 'View'),
            ('APPROVE', 'Approve'),
            ('REJECT', 'Reject'),
        ]
    )
    
    changes = models.JSONField(
        help_text="JSON representation of changes"
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.model_name} by {self.user}"