"""
Django models for users (optional - we're using our RDBMS)
Note: These are just for Django admin, our actual data is in custom RDBMS
"""
from django.db import models

# This is optional - only if you want Django admin integration
class UserProfile(models.Model):
    """Django model for users (optional)"""
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"