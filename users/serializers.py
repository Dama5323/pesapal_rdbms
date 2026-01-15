# web/users/serializers.py
"""
Serializers for Users API
"""
from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    """Serializer for User data"""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=200)
    created_at = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        """Create a new user"""
        from core.services import rdbms_service
        users_table = rdbms_service.get_users_table()
        
        # Generate new ID
        all_users = users_table.select()
        new_id = max([u.get('id', 0) for u in all_users]) + 1 if all_users else 1
        validated_data['id'] = new_id
        validated_data['created_at'] = '2024-01-15'  # Should use actual datetime
        
        users_table.insert(validated_data)
        return validated_data
    
    def update(self, instance, validated_data):
        """Update an existing user"""
        from core.services import rdbms_service
        users_table = rdbms_service.get_users_table()
        
        # Keep the ID
        validated_data['id'] = instance['id']
        if 'created_at' not in validated_data:
            validated_data['created_at'] = instance.get('created_at', '2024-01-15')
        
        users_table.update(validated_data, {'id': instance['id']})
        return validated_data

class UserDetailSerializer(UserSerializer):
    """Serializer for detailed user view"""
    task_count = serializers.SerializerMethodField()
    
    def get_task_count(self, obj):
        """Get count of tasks for this user"""
        from core.services import rdbms_service
        tasks_table = rdbms_service.get_tasks_table()
        tasks = tasks_table.select({'user_id': obj['id']})
        return len(tasks)