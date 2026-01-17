import sys
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the service
from services import rdbms_service

@csrf_exempt
def users_list(request):
    """
    Handle /api/users/ endpoint
    GET: List all users
    POST: Create new user
    """
    if request.method == 'GET':
        users = rdbms_service.get_all_users()
        return JsonResponse({'users': users})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = rdbms_service.create_user(data)
            return JsonResponse({'user': user}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def user_detail(request, user_id):
    """
    Handle /api/users/<id>/ endpoint
    GET: Get user by ID
    PUT: Update user
    DELETE: Delete user
    """
    if request.method == 'GET':
        user = rdbms_service.get_user(user_id)
        if user:
            return JsonResponse({'user': user})
        return JsonResponse({'error': 'User not found'}, status=404)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            success = rdbms_service.update_user(user_id, data)
            if success:
                return JsonResponse({'message': 'User updated successfully'})
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        success = rdbms_service.delete_user(user_id)
        if success:
            return JsonResponse({'message': 'User deleted successfully'})
        return JsonResponse({'error': 'User not found'}, status=404)
    
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)