from django.contrib import admin
from web.rdbms_admin import RDBMSAdminMixin
from .models import Transaction, Invoice


@admin.register(Transaction)
class TransactionAdmin(RDBMSAdminMixin, admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "amount",
        "currency",
        "status",
        "ledger_info",
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "amount", "status")
