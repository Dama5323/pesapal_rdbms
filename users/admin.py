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

    # ✅ Remove all references to username
    list_display = ['email', 'phone_number', 'kyc_status', 'is_staff', 'is_active']
    list_filter = ['kyc_status', 'is_staff', 'is_active']
    search_fields = ['email', 'phone_number']

    # Ordering by email now instead of username
    ordering = ('email',)

    # Fieldsets updated for email-based user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 
                                      'national_id', 'date_of_birth', 'country')}),
        ('KYC & Limits', {'fields': ('kyc_status', 'daily_limit', 'monthly_limit')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Ledger Information', {'fields': (), 'classes': ('collapse',)}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:  # Editing existing user
            return readonly_fields + ('ledger_event_id', 'ledger_hash')
        return readonly_fields

class AccountAdmin(AdminMixin, admin.ModelAdmin):
    list_display = ['account_number', 'user', 'account_type', 'balance', 
                    'currency', 'status', 'ledger_event_id']
    list_filter = ['account_type', 'status', 'currency']
    search_fields = ['account_number', 'user__email']  # ✅ search by email now
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
        from django.contrib import messages
        for account in queryset:
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

# Register models
admin.site.register(User, UserAdmin)
admin.site.register(Account, AccountAdmin)
