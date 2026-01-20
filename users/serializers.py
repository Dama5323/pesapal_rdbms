from rest_framework import serializers
from .models import User, UserProfile, Account

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['address_line_1', 'address_line_2', 'city', 'postal_code',
                 'employment_status', 'occupation', 'employer_name',
                 'preferred_currency', 'notification_preferences']

class AccountSerializer(serializers.ModelSerializer):
    ledger_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'account_type', 'balance',
                 'available_balance', 'currency', 'status', 'interest_rate',
                 'minimum_balance', 'overdraft_limit', 'ledger_event_id',
                 'ledger_hash', 'ledger_info']
        read_only_fields = ['ledger_event_id', 'ledger_hash', 'ledger_info']
    
    def get_ledger_info(self, obj):
        """Get ledger verification info"""
        if obj.ledger_event_id and obj.ledger_hash:
            return {
                'ledger_event_id': obj.ledger_event_id,
                'ledger_hash_short': obj.ledger_hash[:16] + '...' if obj.ledger_hash else None,
                'has_ledger_record': True
            }
        return {'has_ledger_record': False}

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    accounts = AccountSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                 'phone_number', 'national_id', 'date_of_birth', 'country',
                 'kyc_status', 'daily_limit', 'monthly_limit', 'profile', 'accounts']
        read_only_fields = ['kyc_status']
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = User.objects.create_user(**validated_data)
        
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        
        # Create default account
        Account.objects.create(
            user=user,
            account_number=f'ACC{user.id.hex[:8].upper()}',
            account_type='SAVINGS',
            currency='KES'
        )
        
        return user
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile if provided
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            phone_number=validated_data.get('phone_number'),
            password=validated_data['password']
        )
        return user

class UserKYCUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['kyc_status']
        read_only_fields = ['kyc_status']  # Admin only