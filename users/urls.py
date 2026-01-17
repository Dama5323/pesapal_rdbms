# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.users_list, name='users_list'),
    path('<int:user_id>/', views.user_detail, name='user_detail'),
]