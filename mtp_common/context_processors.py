from django.conf import settings
from django.utils.translation import get_language, gettext


def analytics(_):
    return {'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', None)}


def app_environment(_):
    app_git_commit = getattr(settings, 'APP_GIT_COMMIT', None)
    return {
        'APP': getattr(settings, 'APP', None),
        'ENVIRONMENT': getattr(settings, 'ENVIRONMENT', None),
        'APP_BUILD_DATE': getattr(settings, 'APP_BUILD_DATE', None),
        'APP_GIT_COMMIT': app_git_commit,
        'APP_GIT_COMMIT_SHORT': (app_git_commit or 'unknown')[:7],
    }


def govuk_localisation(_):
    html_lang = get_language()
    return {
        'html_lang': html_lang or settings.LANGUAGE_CODE,
        'home_url': '/%s/' % html_lang if html_lang else '/',
        'skip_link_message': gettext('Skip to main content'),
        'homepage_url': 'https://www.gov.uk/',
        'logo_link_title': gettext('Go to the GOV.UK homepage'),
        'global_header_text': 'GOV.UK',
        'crown_copyright_message': gettext('© Crown copyright'),
    }
