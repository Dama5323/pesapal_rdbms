# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserProfile, Account

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number',
            'first_name', 'last_name', 'national_id',
            'date_of_birth', 'country', 'kyc_status',
            'daily_limit', 'monthly_limit',
            'password', 'confirm_password'
        ]
        read_only_fields = ['id', 'kyc_status']
    
    def validate(self, data):
        # Check if passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
            })
        
        # Check if phone number is unique
        if User.objects.filter(phone_number=data.get('phone_number')).exists():
            raise serializers.ValidationError({
                "phone_number": "A user with this phone number already exists."
            })
        
        return data
    
    def create(self, validated_data):
        # Remove confirm_password from validated data
        validated_data.pop('confirm_password')
        
        # Create user with hashed password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            national_id=validated_data.get('national_id'),
            date_of_birth=validated_data.get('date_of_birth'),
            country=validated_data.get('country', 'Kenya')
        )
        
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials.",
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    "User account is disabled.",
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                "Must include 'username' and 'password'.",
                code='authorization'
            )
        
        data['user'] = user
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'address_line_1', 'address_line_2',
            'city', 'postal_code', 'employment_status',
            'occupation', 'employer_name', 'preferred_currency',
            'notification_preferences'
        ]
        read_only_fields = ['id']

class AccountSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'user', 'user_id', 'account_number',
            'account_type', 'balance', 'available_balance',
            'currency', 'status', 'interest_rate',
            'minimum_balance', 'overdraft_limit',
            'created_at', 'opened_date'
        ]
        read_only_fields = [
            'id', 'balance', 'available_balance',
            'created_at', 'opened_date'
        ]
    
    def validate(self, data):
        # Check if user exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=data['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "user_id": "User does not exist."
            })
        
        # Check if account number is unique
        if Account.objects.filter(account_number=data['account_number']).exists():
            raise serializers.ValidationError({
                "account_number": "Account number already exists."
            })
        
        return data
    
    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        
        account = Account.objects.create(
            user=user,
            **validated_data
        )
        
        return account

class BalanceSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    available_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    last_updated = serializers.DateTimeField()