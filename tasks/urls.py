from django.urls import path
from . import views

urlpatterns = [
  path('transactions/create/', views.create_transaction, name='create_transaction'),
  path('transactions/<str:transaction_id>/audit/', views.transaction_audit, name='transaction_audit'),
]