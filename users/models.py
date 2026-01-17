from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import uuid
from django.core.validators import MinLengthValidator, RegexValidator

class User(AbstractUser):
    """
    Custom User model for PesaPal with financial-specific fields
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Override groups and user_permissions to avoid E304 clashes
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',  # unique name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions_set',  # unique name
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
        return f"{self.username} - {self.phone_number}"


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
            
