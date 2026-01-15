from django.shortcuts import render
from django.http import JsonResponse

def dashboard(request):
    """Render the main dashboard"""
    return render(request, 'dashboard.html')

def api_docs(request):
    """Render API documentation page"""
    # Add your API docs context here
    context = {
        'endpoints': [
            {'name': 'Users API', 'url': '/api/users/', 'method': 'GET,POST,PUT,DELETE'},
            {'name': 'Tasks API', 'url': '/api/tasks/', 'method': 'GET,POST,PUT,DELETE'},
            {'name': 'SQL Executor', 'url': '/api/tasks/sql/', 'method': 'POST'},
            {'name': 'Admin Interface', 'url': '/admin/', 'method': 'GET'},
        ]
    }
    return render(request, 'api_docs.html', context)

def sql_executor(request):
    """Render SQL executor page"""
    return render(request, 'sql_executor.html')

def home(request):
    """Home page - redirects to dashboard"""
    return dashboard(request)

def custom_404(request, exception):
    """Custom 404 page"""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 page"""
    return render(request, '500.html', status=500)