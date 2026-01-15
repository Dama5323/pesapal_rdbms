# web/tasks/forms.py
"""
Django forms (optional, for form validation)
"""
from django import forms

class UserForm(forms.Form):
    username = forms.CharField(max_length=100)
    email = forms.EmailField()

class TaskForm(forms.Form):
    title = forms.CharField(max_length=200)
    description = forms.CharField(widget=forms.Textarea)
    user_id = forms.IntegerField()
    status = forms.ChoiceField(choices=[
        ('pending', 'Pending'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed')
    ])