from django.urls import path
from . import views

urlpatterns = [
    # DRF API endpoints
    path('', views.users_list, name='users_list'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('current/', views.current_user, name='current_user'),
    path('<uuid:user_id>/', views.user_detail, name='user_detail'),
    path('<uuid:user_id>/kyc/', views.update_kyc_status, name='update_kyc'),
    path('<uuid:user_id>/accounts/', views.user_accounts, name='user_accounts'),
    
    # RDBMS Integration endpoints
    path('<uuid:user_id>/audit-logs/', views.user_audit_logs, name='user_audit_logs'),
    path('accounts/<str:account_number>/transactions/', 
         views.account_transaction_history, name='account_transactions'),
    
    # Legacy endpoints (for compatibility)
    path('legacy/', views.users_list_legacy, name='users_list_legacy'),
    path('legacy/<uuid:user_id>/', views.user_detail_legacy, name='user_detail_legacy'),
]