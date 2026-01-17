# test_imports.py
import sys
import os

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print(f"Project root: {project_root}")
print(f"Python path: {sys.path[:2]}")

try:
    from services import rdbms_service
    print("✅ Successfully imported rdbms_service from services.py")
    
    # Test it
    print(f"Service type: {type(rdbms_service)}")
    print(f"Methods: {[m for m in dir(rdbms_service) if not m.startswith('_')][:10]}")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    
    # Check what's in services.py
    services_path = os.path.join(project_root, 'services.py')
    if os.path.exists(services_path):
        print(f"services.py exists at: {services_path}")
        with open(services_path, 'r') as f:
            content = f.read()[:500]
            print(f"First 500 chars:\n{content}")
    else:
        print("services.py does not exist!")