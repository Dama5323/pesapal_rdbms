# tasks/views.py
"""
Simple views for Tasks app
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

# Add project root to path
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

class TaskListView(View):
    """List all tasks with JOIN demonstration"""
    
    def get(self, request):
        if not RDBMS_AVAILABLE or not rdbms_service:
            return JsonResponse({
                "error": "RDBMS service not available",
                "tasks": [
                    {"id": 1, "title": "Test Task 1", "user_id": 1},
                    {"id": 2, "title": "Test Task 2", "user_id": 2}
                ]
            })
        
        users_table = rdbms_service.get_table("users")
        tasks_table = rdbms_service.get_table("tasks")
        
        if not users_table or not tasks_table:
            return JsonResponse({"tasks": []})
        
        # Perform JOIN between tasks and users
        try:
            joined_data = tasks_table.join(users_table, "user_id", "id", "INNER")
            
            # Format results
            tasks_with_users = []
            for row in joined_data:
                task_info = {
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "description": row.get("description"),
                    "status": row.get("status"),
                    "priority": row.get("priority"),
                    "user": {
                        "id": row.get("user_id"),
                        "username": row.get("username"),
                        "email": row.get("email")
                    } if row.get("username") else None
                }
                tasks_with_users.append(task_info)
            
            return JsonResponse({
                "message": "JOIN demonstration successful",
                "tasks": tasks_with_users,
                "join_type": "INNER JOIN tasks ON users.id = tasks.user_id"
            })
            
        except Exception as e:
            # If JOIN fails, return tasks without user info
            tasks = tasks_table.select()
            return JsonResponse({
                "message": f"Simple select (JOIN failed: {str(e)})",
                "tasks": tasks
            })

class TaskDetailView(View):
    """Get task by ID"""
    
    def get(self, request, task_id):
        if not RDBMS_AVAILABLE or not rdbms_service:
            return JsonResponse({
                "error": "RDBMS service not available",
                "task": {"id": task_id, "title": "Test Task"}
            })
        
        tasks_table = rdbms_service.get_table("tasks")
        if tasks_table:
            tasks = tasks_table.select({"id": int(task_id)})
            if tasks:
                return JsonResponse({"task": tasks[0]})
        
        return JsonResponse({"error": "Task not found"}, status=404)

class SQLExecutorView(View):
    """Execute raw SQL (demonstrates SQL interface)"""
    
    def post(self, request):
        if not RDBMS_AVAILABLE or not rdbms_service:
            return JsonResponse({
                "error": "RDBMS service not available",
                "message": "Cannot execute SQL"
            })
        
        # Get SQL from POST data
        import json
        try:
            data = json.loads(request.body)
            sql = data.get('sql', '').strip()
            
            if not sql:
                return JsonResponse({"error": "SQL command required"}, status=400)
            
            # Execute SQL
            result = rdbms_service.execute(sql)
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    def get(self, request):
        # Show available SQL commands
        return JsonResponse({
            "available_commands": [
                "SELECT * FROM users",
                "SELECT * FROM tasks",
                "CREATE TABLE ...",
                "INSERT INTO ...",
                "UPDATE ... SET ... WHERE ...",
                "DELETE FROM ... WHERE ..."
            ],
            "example": "POST with JSON: {\"sql\": \"SELECT * FROM users\"}"
        })