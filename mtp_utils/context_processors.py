from django.conf import settings


def analytics(request):
    return {'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', None)}


def app_environment(request):
    return {
        'APP': getattr(settings, 'APP', None),
        'ENVIRONMENT': getattr(settings, 'ENVIRONMENT', None),
    }
