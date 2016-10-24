from django.conf import settings


def analytics(request):
    return {'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', None)}


def app_environment(request):
    app_git_commit = getattr(settings, 'APP_GIT_COMMIT', None)
    return {
        'APP': getattr(settings, 'APP', None),
        'ENVIRONMENT': getattr(settings, 'ENVIRONMENT', None),
        'APP_BUILD_DATE': getattr(settings, 'APP_BUILD_DATE', None),
        'APP_GIT_COMMIT': app_git_commit,
        'APP_GIT_COMMIT_SHORT': (app_git_commit or 'unknown')[:7],
    }
