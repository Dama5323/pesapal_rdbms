from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserProfile, Account
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup initial users and accounts for testing'
    
    def handle(self, *args, **options):
        self.stdout.write("Setting up initial users...")
        
        # Create superuser if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@pesapal.com',
                password='admin123',
                phone_number='+254700000000',
                kyc_status='VERIFIED'
            )
            self.stdout.write(self.style.SUCCESS("✓ Created superuser: admin/admin123"))
        
        # Create test users
        test_users = [
            {
                'username': 'merchant1',
                'email': 'merchant1@example.com',
                'password': 'password123',
                'phone_number': '+254711111111',
                'kyc_status': 'VERIFIED'
            },
            {
                'username': 'customer1', 
                'email': 'customer1@example.com',
                'password': 'password123',
                'phone_number': '+254722222222',
                'kyc_status': 'VERIFIED'
            },
            {
                'username': 'agent1',
                'email': 'agent1@example.com',
                'password': 'password123',
                'phone_number': '+254733333333',
                'kyc_status': 'PENDING'
            }
        ]
        
        for user_data in test_users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    phone_number=user_data['phone_number'],
                    kyc_status=user_data['kyc_status']
                )
                
                # Create profile
                UserProfile.objects.create(
                    user=user,
                    address_line_1='123 Main St',
                    city='Nairobi',
                    postal_code='00100',
                    preferred_currency='KES'
                )
                
                # Create accounts
                Account.objects.create(
                    user=user,
                    account_number=f'ACC{user.id.hex[:8].upper()}',
                    account_type='SAVINGS',
                    balance=10000.00,
                    available_balance=10000.00,
                    currency='KES'
                )
                
                self.stdout.write(self.style.SUCCESS(f"✓ Created user: {user.username}"))
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("✅ User setup complete!"))
        self.stdout.write("="*50)
        self.stdout.write(f"Total Users: {User.objects.count()}")
        self.stdout.write(f"Total Accounts: {Account.objects.count()}")
        self.stdout.write("\n🔑 Login credentials:")
        self.stdout.write("  Admin: admin / admin123")
        self.stdout.write("  Merchant: merchant1 / password123")
        self.stdout.write("  Customer: customer1 / password123")