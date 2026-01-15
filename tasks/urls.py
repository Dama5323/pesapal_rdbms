# tasks/urls.py
from django.urls import path
from .views import TaskListView, TaskDetailView, SQLExecutorView

urlpatterns = [
    path('', TaskListView.as_view(), name='task-list'),
    path('<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path('sql/', SQLExecutorView.as_view(), name='sql-executor'),
]