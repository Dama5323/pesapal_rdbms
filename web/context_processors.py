from django.conf import settings

def global_context(request):
    """Add global context to all templates"""
    return {
        'APP_NAME': 'PesaPal RDBMS',
        'APP_VERSION': '1.0.0',
        'DEBUG': settings.DEBUG,
    }