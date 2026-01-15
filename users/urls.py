# users/urls.py
from django.urls import path
from .views import UserListView, UserDetailView, create_user

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('create/', create_user, name='create-user'),
]