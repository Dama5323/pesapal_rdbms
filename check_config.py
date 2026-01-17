# check_config.py
import os
import sys

# Add your project to path
sys.path.append('.')

# Load Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')

import django
django.setup()

from django.conf import settings

print("=" * 50)
print("DATABASE CONFIGURATION CHECK")
print("=" * 50)
print(f"Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Name: {settings.DATABASES['default']['NAME']}")
print(f"User: {settings.DATABASES['default'].get('USER', 'Not set')}")
print(f"Host: {settings.DATABASES['default'].get('HOST', 'Not set')}")
print("=" * 50)