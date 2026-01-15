# web/tasks/serializers.py
"""
Serializers for Tasks API
"""
from rest_framework import serializers

class TaskSerializer(serializers.Serializer):
    """Serializer for Task data"""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    user_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=['pending', 'in_progress', 'completed', 'cancelled'],
        default='pending'
    )
    priority = serializers.ChoiceField(
        choices=['low', 'medium', 'high', 'critical'],
        default='medium'
    )
    created_at = serializers.CharField(read_only=True)
    due_date = serializers.CharField(required=False)
    
    def create(self, validated_data):
        """Create a new task"""
        from core.services import rdbms_service
        tasks_table = rdbms_service.get_tasks_table()
        
        # Generate new ID
        all_tasks = tasks_table.select()
        new_id = max([t.get('id', 0) for t in all_tasks]) + 1 if all_tasks else 1
        validated_data['id'] = new_id
        validated_data['created_at'] = '2024-01-15'  # Should use actual datetime
        
        tasks_table.insert(validated_data)
        return validated_data
    
    def update(self, instance, validated_data):
        """Update an existing task"""
        from core.services import rdbms_service
        tasks_table = rdbms_service.get_tasks_table()
        
        # Keep the ID
        validated_data['id'] = instance['id']
        if 'created_at' not in validated_data:
            validated_data['created_at'] = instance.get('created_at', '2024-01-15')
        
        tasks_table.update(validated_data, {'id': instance['id']})
        return validated_data

class TaskWithUserSerializer(TaskSerializer):
    """Serializer for task with user details (JOIN result)"""
    user = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        """Get user details for this task"""
        from core.services import rdbms_service
        users_table = rdbms_service.get_users_table()
        user_id = obj.get('user_id')
        
        if user_id:
            users = users_table.select({'id': user_id})
            if users:
                return {
                    'id': users[0].get('id'),
                    'username': users[0].get('username'),
                    'full_name': users[0].get('full_name'),
                    'email': users[0].get('email')
                }
        return None