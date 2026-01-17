import sys
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Add the project root to Python path so we can import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the service
from services import rdbms_service

@csrf_exempt
def tasks_list(request):
    """Handle /api/tasks/ endpoint (with JOIN demonstration)"""
    if request.method == 'GET':
        # Get tasks with user info (JOIN)
        tasks = rdbms_service.get_all_tasks()
        
        # Format for better display
        formatted_tasks = []
        for task in tasks:
            formatted = {
                'id': task.get('id'),
                'title': task.get('title'),
                'description': task.get('description'),
                'status': task.get('status'),
                'priority': task.get('priority'),
                'user': {
                    'id': task.get('user_id'),
                    'name': task.get('users_name', 'Unknown'),
                    'email': task.get('users_email', '')
                } if 'users_name' in task else {'id': task.get('user_id')}
            }
            formatted_tasks.append(formatted)
        
        return JsonResponse({'tasks': formatted_tasks})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            task = rdbms_service.create_task(data)
            return JsonResponse({'task': task}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def task_detail(request, task_id):
    """Handle /api/tasks/<id>/ endpoint"""
    if request.method == 'GET':
        task = rdbms_service.get_task(task_id)
        if task:
            return JsonResponse({'task': task})
        return JsonResponse({'error': 'Task not found'}, status=404)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            success = rdbms_service.update_task(task_id, data)
            if success:
                return JsonResponse({'message': 'Task updated successfully'})
            return JsonResponse({'error': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        success = rdbms_service.delete_task(task_id)
        if success:
            return JsonResponse({'message': 'Task deleted successfully'})
        return JsonResponse({'error': 'Task not found'}, status=404)
    
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def sql_executor(request):
    """Handle /api/tasks/sql/ endpoint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sql = data.get('query', '')
            
            if not sql:
                return JsonResponse({'error': 'No SQL query provided'}, status=400)
            
            result = rdbms_service.execute_sql(sql)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST method required'}, status=405)

@csrf_exempt  
def join_demo(request):
    """Special endpoint to demonstrate JOIN operations"""
    if request.method == 'GET':
        try:
            # Create fresh demo data
            users = [
                {'id': 1, 'username': 'alice', 'email': 'alice@example.com', 'first_name': 'Alice', 'last_name': 'Smith', 'is_active': True},
                {'id': 2, 'username': 'bob', 'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Johnson', 'is_active': True},
                {'id': 3, 'username': 'charlie', 'email': 'charlie@example.com', 'first_name': 'Charlie', 'last_name': 'Brown', 'is_active': True},
            ]
            
            tasks = [
                {'id': 1, 'user_id': 1, 'title': 'Design database schema', 'description': 'Create ERD diagram', 'status': 'completed', 'priority': 'high'},
                {'id': 2, 'user_id': 1, 'title': 'Implement API', 'description': 'Build REST endpoints', 'status': 'in_progress', 'priority': 'high'},
                {'id': 3, 'user_id': 2, 'title': 'Write tests', 'description': 'Unit tests for all modules', 'status': 'pending', 'priority': 'medium'},
                {'id': 4, 'user_id': 3, 'title': 'Documentation', 'description': 'User guide and API docs', 'status': 'pending', 'priority': 'low'},
            ]
            
            # Clear existing tables if they exist
            if 'users' in rdbms_service.list_tables():
                rdbms_service.execute_sql("DROP TABLE users")
            if 'tasks' in rdbms_service.list_tables():
                rdbms_service.execute_sql("DROP TABLE tasks")
            
            # Create fresh tables
            rdbms_service._ensure_tables()
            
            # Insert sample data
            for user in users:
                rdbms_service.create_user(user)
            
            for task in tasks:
                rdbms_service.create_task(task)
            
            # Execute JOIN queries
            join_results = []
            
            # INNER JOIN
            inner_join = rdbms_service.execute_sql(
                "SELECT users.username, tasks.title, tasks.status FROM users JOIN tasks ON users.id = tasks.user_id"
            )
            join_results.append({
                'type': 'INNER JOIN',
                'description': 'Returns matching records from both tables',
                'sql': 'SELECT users.username, tasks.title, tasks.status FROM users JOIN tasks ON users.id = tasks.user_id',
                'results': inner_join.get('data', [])[:3],
                'count': inner_join.get('count', 0)
            })
            
            # Complex JOIN with WHERE
            complex_join = rdbms_service.execute_sql(
                "SELECT users.username, tasks.title, tasks.priority FROM users JOIN tasks ON users.id = tasks.user_id WHERE tasks.priority = 'high'"
            )
            join_results.append({
                'type': 'JOIN with WHERE',
                'description': 'High priority tasks with assigned users',
                'sql': "SELECT users.username, tasks.title, tasks.priority FROM users JOIN tasks ON users.id = tasks.user_id WHERE tasks.priority = 'high'",
                'results': complex_join.get('data', []),
                'count': complex_join.get('count', 0)
            })
            
            return JsonResponse({
                'status': 'success',
                'message': 'JOIN demonstration setup complete',
                'tables_created': ['users', 'tasks'],
                'sample_data_inserted': {
                    'users': len(users),
                    'tasks': len(tasks)
                },
                'join_demonstrations': join_results
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'GET method required'}, status=405)