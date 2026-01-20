from rest_framework import serializers
from .models import Transaction, Invoice, AuditLog
from users.models import Account, User
from django.utils import timezone
from django.db import models
import uuid

class TransactionSerializer(serializers.ModelSerializer):
    from_account_number = serializers.CharField(
        source='from_account.account_number',
        read_only=True
    )
    to_account_number = serializers.CharField(
        source='to_account.account_number',
        read_only=True
    )
    from_user_name = serializers.CharField(
        source='from_account.user.get_full_name',
        read_only=True
    )
    to_user_name = serializers.CharField(
        source='to_account.user.get_full_name',
        read_only=True
    )
    
    from_account_id = serializers.UUIDField(write_only=True)
    to_account_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'internal_reference',
            'from_account', 'from_account_id', 'from_account_number', 'from_user_name',
            'to_account', 'to_account_id', 'to_account_number', 'to_user_name',
            'amount', 'currency', 'exchange_rate', 'converted_amount',
            'transaction_type', 'status', 'fee_amount', 'tax_amount', 'net_amount',
            'description', 'payment_method',
            'initiated_at', 'processed_at', 'completed_at',
            'initiated_by', 'processed_by',
            'reconciled', 'reconciled_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'internal_reference',
            'from_account', 'to_account',
            'exchange_rate', 'converted_amount',
            'fee_amount', 'tax_amount', 'net_amount',
            'initiated_at', 'processed_at', 'completed_at',
            'initiated_by', 'processed_by',
            'reconciled', 'reconciled_at'
        ]
    
    def validate(self, data):
        # Check if accounts exist
        try:
            from_account = Account.objects.get(id=data['from_account_id'])
            to_account = Account.objects.get(id=data['to_account_id'])
        except Account.DoesNotExist:
            raise serializers.ValidationError({
                "account_id": "One or both accounts do not exist."
            })
        
        # Check if accounts are active
        if from_account.status != 'ACTIVE':
            raise serializers.ValidationError({
                "from_account_id": "From account is not active."
            })
        
        if to_account.status != 'ACTIVE':
            raise serializers.ValidationError({
                "to_account_id": "To account is not active."
            })
        
        # Check if accounts have same currency
        if from_account.currency != to_account.currency:
            raise serializers.ValidationError({
                "currency": "Accounts must have the same currency for direct transfers."
            })
        
        # Check if user has sufficient balance
        if from_account.available_balance < data['amount']:
            raise serializers.ValidationError({
                "amount": "Insufficient funds in from account."
            })
        
        # Check daily limit
        user = from_account.user
        daily_total = Transaction.objects.filter(
            from_account=from_account,
            initiated_at__date=timezone.now().date(),
            status='COMPLETED'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        if daily_total + data['amount'] > user.daily_limit:
            raise serializers.ValidationError({
                "amount": f"Daily limit exceeded. Remaining: {user.daily_limit - daily_total}"
            })
        
        data['from_account'] = from_account
        data['to_account'] = to_account
        
        return data
    
    def create(self, validated_data):
        # Generate transaction IDs
        validated_data['transaction_id'] = f"TX{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        validated_data['internal_reference'] = f"INT{uuid.uuid4().hex[:16].upper()}"
        
        # Set initiated by user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['initiated_by'] = request.user
        
        # Calculate net amount (for now, same as amount)
        validated_data['net_amount'] = validated_data['amount']
        
        transaction = Transaction.objects.create(**validated_data)
        return transaction

class InvoiceSerializer(serializers.ModelSerializer):
    merchant_name = serializers.CharField(
        source='merchant.get_full_name',
        read_only=True
    )
    merchant_email = serializers.EmailField(
        source='merchant.email',
        read_only=True
    )
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'merchant', 'merchant_name', 'merchant_email',
            'customer_name', 'customer_email', 'customer_phone',
            'amount', 'currency', 'status', 'status_display',
            'issue_date', 'due_date', 'paid_date',
            'paid_amount', 'remaining_amount',
            'items', 'notes', 'terms_and_conditions',
            'transaction', 'created_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'remaining_amount',
            'paid_date', 'transaction', 'created_at'
        ]
    
    def validate(self, data):
        # Validate due date is in the future
        if 'due_date' in data and data['due_date'] < timezone.now().date():
            raise serializers.ValidationError({
                "due_date": "Due date must be in the future."
            })
        
        # Validate items if provided
        if 'items' in data:
            if not isinstance(data['items'], list):
                raise serializers.ValidationError({
                    "items": "Items must be a list."
                })
            
            total = 0
            for i, item in enumerate(data['items']):
                if not all(k in item for k in ['description', 'quantity', 'unit_price']):
                    raise serializers.ValidationError({
                        "items": f"Item {i} missing required fields (description, quantity, unit_price)."
                    })
                
                total += item['quantity'] * item['unit_price']
            
            if 'amount' in data and abs(total - data['amount']) > 0.01:
                raise serializers.ValidationError({
                    "items": f"Items total ({total}) does not match invoice amount ({data['amount']})."
                })
            else:
                data['amount'] = total
        
        return data
    
    def create(self, validated_data):
        # Generate invoice number
        validated_data['invoice_number'] = f"INV{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate remaining amount
        validated_data['remaining_amount'] = validated_data['amount']
        
        invoice = Invoice.objects.create(**validated_data)
        return invoice

class TransactionStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating transaction status
    """
    status = serializers.ChoiceField(choices=[
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('HOLD', 'On Hold'),
    ])
    
    notes = serializers.CharField(required=False, allow_blank=True)

class PaymentLinkSerializer(serializers.Serializer):
    """
    Serializer for generating payment links
    """
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='KES')
    description = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField(required=False)
    customer_name = serializers.CharField(max_length=200, required=False)
    expires_at = serializers.DateTimeField(required=False)
    
    def validate(self, data):
        # Validate expiry date is in the future
        if 'expires_at' in data and data['expires_at'] <= timezone.now():
            raise serializers.ValidationError({
                "expires_at": "Expiry date must be in the future."
            })
        
        return data

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'model_name', 'object_id',
            'user', 'user_name', 'user_email',
            'action', 'changes',
            'ip_address', 'user_agent',
            'timestamp'
        ]
        read_only_fields = fields