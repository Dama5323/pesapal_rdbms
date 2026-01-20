from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Account

# Try to import RDBMS admin mixin
try:
    from web.rdbms_admin import RDBMSAdminMixin
    AdminMixin = RDBMSAdminMixin
except ImportError:
    class AdminMixin:
        pass


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class AccountInline(admin.TabularInline):
    model = Account
    extra = 0
    readonly_fields = ['ledger_event_id', 'ledger_hash']
    fields = ['account_number', 'account_type', 'balance', 'currency', 'status', 'ledger_event_id']

class UserAdmin(BaseUserAdmin, AdminMixin):
    inlines = [UserProfileInline, AccountInline]
    list_display = ['username', 'email', 'phone_number', 'kyc_status', 'is_staff', 'ledger_info']
    list_filter = ['kyc_status', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'phone_number']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('PesaPal Information', {
            'fields': ('phone_number', 'national_id', 'date_of_birth', 
                      'country', 'kyc_status', 'daily_limit', 'monthly_limit')
        }),
        ('Ledger Information', {
            'fields': (),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:  # Editing an existing object
            return readonly_fields + ('ledger_event_id', 'ledger_hash')
        return readonly_fields

class AccountAdmin(AdminMixin, admin.ModelAdmin):
    list_display = ['account_number', 'user', 'account_type', 'balance', 
                   'currency', 'status', 'ledger_info', 'verify_integrity']
    list_filter = ['account_type', 'status', 'currency']
    search_fields = ['account_number', 'user__username']
    readonly_fields = ['ledger_event_id', 'ledger_hash']
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_number', 'account_type')
        }),
        ('Balance Information', {
            'fields': ('balance', 'available_balance', 'currency')
        }),
        ('Account Settings', {
            'fields': ('status', 'interest_rate', 'minimum_balance', 'overdraft_limit')
        }),
        ('Ledger Information', {
            'fields': ('ledger_event_id', 'ledger_hash'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['record_to_ledger_action']
    
    def record_to_ledger_action(self, request, queryset):
        """Record selected accounts to ledger"""
        from django.contrib import messages
        
        for account in queryset:
            # Record balance as a transaction
            try:
                from services import rdbms_service
                transaction_data = {
                    'transaction_id': f'ACCOUNT_INIT_{account.account_number}',
                    'amount': float(account.balance),
                    'currency': account.currency,
                    'from_account': 'system',
                    'to_account': account.account_number,
                    'status': 'COMPLETED',
                    'type': 'ACCOUNT_CREATION'
                }
                result = rdbms_service.record_transaction(transaction_data)
                
                if result.get('success'):
                    account.ledger_event_id = result.get('ledger_event_id')
                    account.ledger_hash = result.get('hash')
                    account.save()
                    self.message_user(
                        request,
                        f"Account {account.account_number} recorded to ledger",
                        level=messages.SUCCESS
                    )
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to record {account.account_number}: {e}",
                    level=messages.ERROR
                )
    
    record_to_ledger_action.short_description = "📝 Record selected accounts to ledger"

admin.site.register(User, UserAdmin)
admin.site.register(Account, AccountAdmin)