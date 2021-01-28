from django.conf import settings
from django.utils.translation import get_language, gettext

from mtp_common.analytics import AnalyticsPolicy, genericised_pageview


def analytics(request):
    return {
        'analytics_policy': AnalyticsPolicy(request),
        'default_google_analytics_pageview': genericised_pageview(request),
    }


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
    moj_internal_site = getattr(settings, 'MOJ_INTERNAL_SITE', False)
    if moj_internal_site:
        homepage_url = 'https://intranet.noms.gsi.gov.uk/'
        logo_link_title = gettext('Go to the HMPPS Intranet')
        global_header_text = gettext('HMPPS')
    else:
        homepage_url = 'https://www.gov.uk/'
        logo_link_title = gettext('Go to the GOV.UK homepage')
        global_header_text = 'GOV.UK'
    html_lang = get_language()
    return {
        'moj_internal_site': moj_internal_site,
        'html_lang': html_lang or settings.LANGUAGE_CODE,
        'home_url': '/%s/' % html_lang if html_lang else '/',
        'homepage_url': homepage_url,
        'logo_link_title': logo_link_title,
        'global_header_text': global_header_text,
    }
