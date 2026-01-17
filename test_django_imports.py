# test_django_imports.py
import sys
import os

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import django
    django.setup()
    
    # Try to import views
    from users import views as user_views
    from tasks import views as task_views
    
    print("✅ Successfully imported Django views")
    print(f"  User views: {dir(user_views)[:5]}...")
    print(f"  Task views: {dir(task_views)[:5]}...")
    
    # Test service import from views
    print("\n✅ Testing service imports from views...")
    
    # Simulate what views do
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services import rdbms_service
    
    print(f"  Service: {rdbms_service}")
    print(f"  Can get users: {hasattr(rdbms_service, 'get_all_users')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()