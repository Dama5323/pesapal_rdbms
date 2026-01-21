# users/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    """Authenticate using email instead of username"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by email
            user = UserModel.objects.get(email=username)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            # Try username as well (if you still use usernames)
            try:
                user = UserModel.objects.get(username=username)
                if user.check_password(password):
                    return user
            except UserModel.DoesNotExist:
                return None
        except Exception:
            return None
    
    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None