"""
URL configuration for web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for web project.
"""

from django.contrib import admin
from django.urls import path, include
from . import views  
from django.http import JsonResponse 
from web.rdbms_admin import rdbms_admin_site
import tasks.views as tasks_views
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

@require_GET
def logout_get_view(request):
    """Handle GET requests for logout (redirects to POST form)"""
    return render(request, 'auth/logout_confirmation.html')

@require_POST
def logout_post_view(request):
    """Handle POST requests for logout"""
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def logout_view(request):
    """Handle both GET and POST for logout"""
    if request.method == 'POST':
        return logout_post_view(request)
    return logout_get_view(request)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Users and Tasks API endpoints  
    path('api/users/', include('users.urls')),
    path('api/tasks/', include('tasks.urls')),
    path('rdbms-admin/', rdbms_admin_site.urls, name='rdbms_admin'),

    # API Documentation 
    path('api/docs/', views.api_docs, name='api_docs'),
    
    # Main pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # API Documentation
    path('docs/', views.api_docs, name='api_docs'),
    
    # SQL Executor
    path('sql/', views.sql_executor, name='sql_executor'),
    
    # Health check endpoint
    path('health/', lambda request: JsonResponse({'status': 'healthy'})),

    # API URLs for RDBMS Integration
    path('api/transactions/create/', tasks_views.create_transaction, name='create_transaction'),
    path('api/transactions/<str:transaction_id>/audit/', tasks_views.transaction_audit, name='transaction_audit'),
    path('api/ledgers/verify/', tasks_views.verify_all_ledgers, name='verify_ledgers'),
    path('api/financial/sql/', tasks_views.execute_financial_sql, name='execute_financial_sql'),
    path('api/financial/report/', tasks_views.financial_report, name='financial_report'),
    
    # Transaction pages
    path('transactions/', views.transactions_view, name='transactions'),
    path('transactions/create/', views.create_transaction_view, name='create_transaction'),
    
    # Ledger and Audit
    path('ledger/', views.ledger_view, name='ledger'),
    path('audit/', views.audit_view, name='audit'),
    
    # Reports and Profile
    path('reports/', views.reports_view, name='reports'),
    path('profile/', views.profile_view, name='profile'),
    
    # Auth pages
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Status page (only for API root)
    path('api/', lambda request: JsonResponse({
        'status': 'PesaPal RDBMS API',
        'endpoints': {
            'admin': '/admin/',
            'rdbms_admin': '/rdbms-admin/',
            'create_transaction': '/api/transactions/create/',
            'verify_ledgers': '/api/ledgers/verify/',
            'financial_report': '/api/financial/report/'
        }
    }), name='api_root'),
]

# Error handlers
handler404 = views.custom_404
handler500 = views.custom_500