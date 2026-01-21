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
from django.contrib import admin
from django.urls import path, include
from . import views  
from django.http import JsonResponse 
from web.rdbms_admin import rdbms_admin_site
import tasks.views as tasks_views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Users and Tasks API endpoints  
    path('api/users/', include('users.urls')),
    path('api/tasks/', include('tasks.urls')),
    path('rdbms-admin/', rdbms_admin_site.urls, name='rdbms_admin'),

    # API Documentation 
    path('api/docs/', views.api_docs, name='api_docs'),
    
    # Dashboard and main pages
    path('', views.dashboard, name='dashboard'),
    path('home/', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # API Documentation
    path('docs/', views.api_docs, name='api_docs'),
    path('api-docs/', views.api_docs, name='api_docs'),
    
    # SQL Executor
    path('sql/', views.sql_executor, name='sql_executor'),
    path('sql-executor/', views.sql_executor, name='sql_executor'),
    
    # Include your API app URLs (if you have a separate app for API)
    # path('api/', include('api.urls')),
    
    # Health check endpoint
    path('health/', lambda request: JsonResponse({'status': 'healthy'})),

    # API URLs for RDBMS Integration
    path('api/transactions/create/', tasks_views.create_transaction, name='create_transaction'),
    path('api/transactions/<str:transaction_id>/audit/', tasks_views.transaction_audit, name='transaction_audit'),
    path('api/ledgers/verify/', tasks_views.verify_all_ledgers, name='verify_ledgers'),
    path('api/financial/sql/', tasks_views.execute_financial_sql, name='execute_financial_sql'),
    path('api/financial/report/', tasks_views.financial_report, name='financial_report'),
    
    # Main pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('transactions/create/', views.create_transaction_view, name='create_transaction'),
    path('ledger/', views.ledger_view, name='ledger'),
    path('audit/', views.audit_view, name='audit'),
    path('reports/', views.reports_view, name='reports'),
    path('profile/', views.profile_view, name='profile'),
    
    # Auth pages
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    
     # Simple status page
    path('', lambda request: JsonResponse({
        'status': 'PesaPal RDBMS API',
        'endpoints': {
            'admin': '/admin/',
            'rdbms_admin': '/rdbms-admin/',
            'create_transaction': '/api/transactions/create/',
            'verify_ledgers': '/api/ledgers/verify/',
            'financial_report': '/api/financial/report/'
        }
    }), name='home'),
]

# Error handlers
handler404 = views.custom_404
handler500 = views.custom_500