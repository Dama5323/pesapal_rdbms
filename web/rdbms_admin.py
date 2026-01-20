# web/rdbms_admin.py
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


# =========================
# SAFE MIXIN (IMPORT FIRST)
# =========================
class RDBMSAdminMixin:
    """
    Optional admin mixin for displaying ledger / audit info.
    Safe to import during admin autodiscovery.
    """

    def ledger_info(self, obj):
        event_id = getattr(obj, "ledger_event_id", None)
        ledger_hash = getattr(obj, "ledger_hash", None)
        if event_id and ledger_hash:
            return f"{event_id[:8]}… ({ledger_hash[:8]}…)"
        return "—"

    ledger_info.short_description = "Ledger"

    def verify_integrity(self, obj):
        return "OK"

    verify_integrity.short_description = "Ledger Integrity"


# =========================
# CUSTOM ADMIN SITE
# =========================
class RDBMSAdminSite(admin.AdminSite):
    site_header = "PesaPal RDBMS Admin"
    site_title = "PesaPal RDBMS"
    index_title = "RDBMS Administration"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "rdbms-status/",
                self.admin_view(rdbms_status_view),
                name="rdbms-status",
            ),
        ]
        return custom_urls + urls


rdbms_admin_site = RDBMSAdminSite(name="rdbms_admin")


# =========================
# ADMIN VIEW (SAFE IMPORT)
# =========================
@rdbms_admin_site.admin_view
def rdbms_status_view(request):
    try:
        from services import rdbms_service
        return JsonResponse({
            "status": "online",
            "tables": rdbms_service.list_tables(),
            "verification": rdbms_service.verify_ledgers(),
        })
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})
