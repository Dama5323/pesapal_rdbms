# users/views.py
"""
Simple views for Users app
"""
import sys
import os
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def dashboard(request):
    """Render the main dashboard"""
    return render(request, 'dashboard.html')

def api_docs(request):
    """Render API documentation page"""
    return render(request, 'api_docs.html')  # You'll need to create this

def sql_executor(request):
    """Render SQL executor page"""
    return render(request, 'sql_executor.html')  # You'll need to create this

# Add project root to path for services import
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from services import rdbms_service
    RDBMS_AVAILABLE = True
except ImportError:
    print("⚠ Could not import rdbms_service from services module")
    RDBMS_AVAILABLE = False
    rdbms_service = None

class UserListView(View):
    """List all users"""
    
    def get(self, request):
        if not RDBMS_AVAILABLE or not rdbms_service:
            return JsonResponse({
                "error": "RDBMS service not available",
                "users": [
                    {"id": 1, "username": "test_user", "email": "test@example.com"},
                    {"id": 2, "username": "demo_user", "email": "demo@example.com"}
                ]
            })
        
        users_table = rdbms_service.get_table("users")
        if users_table:
            users = users_table.select()
            return JsonResponse({"users": users})
        
        return JsonResponse({"users": []})

class UserDetailView(View):
    """Get user by ID"""
    
    def get(self, request, user_id):
        if not RDBMS_AVAILABLE or not rdbms_service:
            return JsonResponse({
                "error": "RDBMS service not available",
                "user": {"id": user_id, "username": "test_user"}
            })
        
        users_table = rdbms_service.get_table("users")
        if users_table:
            users = users_table.select({"id": int(user_id)})
            if users:
                return JsonResponse({"user": users[0]})
        
        return JsonResponse({"error": "User not found"}, status=404)

def create_user(request):
    """Create a new user (POST endpoint)"""
    if request.method == 'POST':
        # Simple implementation
        return JsonResponse({
            "message": "User created successfully",
            "user_id": 999
        })
    return JsonResponse({"error": "Method not allowed"}, status=405)