from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import uuid
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    """Custom manager for User model with email as username"""
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):  
    """
    Custom User model for PesaPal with financial-specific fields
    """
    username = None  
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  

    # IMPORTANT: Assign the custom manager
    objects = UserManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Note: You have email defined twice, remove this duplicate
    # email = models.EmailField(_('email address'), unique=True)
    
    email = models.EmailField(_('email address'), unique=True)

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',  
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions_set',  
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    # Your custom fields
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+254712345678'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        unique=True,
        help_text="Required for mobile money transactions"
    )
    national_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        validators=[MinLengthValidator(5)],
        help_text="National ID number for KYC compliance"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, default='Kenya')

    KYC_STATUS = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    ]
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS, default='PENDING')

    daily_limit = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2, default=1000000.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.email}"
    
    def save(self, *args, **kwargs):
        """Override save to add audit logging"""
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        # Try to log audit if service is available
        try:
            from services import rdbms_service
            changes = {
                'model': 'User',
                'object_id': str(self.id),
                'action': 'CREATE' if is_new else 'UPDATE',
                'fields': {
                    'email': self.email,
                    'kyc_status': self.kyc_status
                }
            }
            rdbms_service.log_audit(
                model_name='User',
                object_id=str(self.id),
                action='CREATE' if is_new else 'UPDATE',
                user_id=str(self.id) if not is_new else 'system',
                changes=changes
            )
        except ImportError:
            pass  # Silently fail if service not available

class UserProfile(models.Model):
    """
    Extended profile information for users
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Address information
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Employment information
    employment_status = models.CharField(
        max_length=50,
        choices=[
            ('EMPLOYED', 'Employed'),
            ('SELF_EMPLOYED', 'Self-Employed'),
            ('UNEMPLOYED', 'Unemployed'),
            ('STUDENT', 'Student'),
        ],
        default='EMPLOYED'
    )
    
    occupation = models.CharField(max_length=100, blank=True)
    employer_name = models.CharField(max_length=200, blank=True)
    
    # Financial preferences
    preferred_currency = models.CharField(
        max_length=3,
        default='KES',
        choices=[
            ('KES', 'Kenyan Shilling'),
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
            ('GBP', 'British Pound'),
        ]
    )
    
    notification_preferences = models.JSONField(
        default=dict,
        help_text="User notification settings"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"Profile for {self.user.username}"


class Account(models.Model):
    """
    Financial account for users (like bank account)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='accounts'
    )
    
    # LEDGER FIELDS
    ledger_event_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Immutable ledger event ID for balance changes"
    )
    
    ledger_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Cryptographic hash from ledger"
    )
    
    # Account details
    account_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique account identifier"
    )
    
    ACCOUNT_TYPES = [
        ('SAVINGS', 'Savings Account'),
        ('CURRENT', 'Current Account'),
        ('BUSINESS', 'Business Account'),
        ('MERCHANT', 'Merchant Account'),
        ('ESCROW', 'Escrow Account'),
    ]
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        default='SAVINGS'
    )
    
    # Balance information
    balance = models.DecimalField(
        max_digits=15,  # Up to 999,999,999,999.99
        decimal_places=2,
        default=0.00
    )
    
    available_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Balance minus any holds/limits"
    )
    
    currency = models.CharField(
        max_length=3,
        default='KES',
        choices=[
            ('KES', 'Kenyan Shilling'),
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
            ('GBP', 'British Pound'),
        ]
    )
    
    # Account status
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'),
        ('FROZEN', 'Frozen'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    
    # Account metadata
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Annual interest rate in percentage"
    )
    
    minimum_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    
    overdraft_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    opened_date = models.DateField(auto_now_add=True)
    closed_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=models.F('minimum_balance')),
                name='balance_above_minimum'
            )
        ]
        
    def __str__(self):
        return f"{self.account_number} - {self.user.username} ({self.balance} {self.currency})"
    
    def save(self, *args, **kwargs):
        """Override save to record balance changes to ledger"""
        # Check if this is an update and balance changed
        if self.pk:
            old_account = Account.objects.get(pk=self.pk)
            balance_changed = old_account.balance != self.balance
        else:
            balance_changed = False
            
        super().save(*args, **kwargs)
        
        # Record balance change to ledger
        if balance_changed:
            self.record_balance_change_to_ledger(old_account.balance)
    
    def record_balance_change_to_ledger(self, old_balance):
        """Record balance change to immutable ledger"""
        try:
            from services import rdbms_service
            
            transaction_data = {
                'id': str(self.id) + '_' + str(uuid.uuid4())[:8],
                'transaction_id': f'BALANCE_{self.account_number}_{uuid.uuid4().hex[:8]}',
                'amount': float(self.balance - old_balance),
                'currency': self.currency,
                'from_account': 'system' if self.balance > old_balance else self.account_number,
                'to_account': self.account_number if self.balance > old_balance else 'system',
                'status': 'COMPLETED',
                'type': 'BALANCE_ADJUSTMENT',
                'metadata': {
                    'account': self.account_number,
                    'old_balance': float(old_balance),
                    'new_balance': float(self.balance),
                    'change': float(self.balance - old_balance),
                    'reason': 'balance_adjustment'
                }
            }
            
            result = rdbms_service.record_transaction(transaction_data)
            
            if result.get('success'):
                self.ledger_event_id = result.get('ledger_event_id')
                self.ledger_hash = result.get('hash')
                # Save without triggering save() again
                Account.objects.filter(pk=self.pk).update(
                    ledger_event_id=self.ledger_event_id,
                    ledger_hash=self.ledger_hash
                )
                
        except ImportError:
            pass  # Silently fail if service not available