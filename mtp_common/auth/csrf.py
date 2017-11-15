from threading import local

from django.contrib import messages
from django.http.request import QueryDict
from django.middleware.csrf import CsrfViewMiddleware as DjangoCsrfViewMiddleware, \
    REASON_NO_CSRF_COOKIE, REASON_NO_REFERER
from django.utils.translation import gettext as _

_csrf_failed_view = local()


def csrf_failure(request, reason=''):
    """
    CSRF-failure view which converts the failed POST request into a GET
    and calls the original view with a sensible error message presented
    to the user.
    :param request: the HttpRequest
    :param reason: non-localised failure description
    """
    if _csrf_failed_view.no_moj_csrf:
        from django.views.csrf import csrf_failure

        return csrf_failure(request, reason=reason)

    # present a sensible error message to users
    if reason == REASON_NO_CSRF_COOKIE:
        reason = _('Please try again.') + ' ' + \
                 _('Make sure you haven’t disabled cookies.')
    elif reason == REASON_NO_REFERER:
        reason = _('Please try again.') + ' ' + \
                 _('Make sure you are using a modern web browser '
                   'such as Firefox or Google Chrome.')
    else:
        reason = _('Your browser failed a security check.') + ' ' + \
                 _('Please try again.')
    messages.error(request, reason)

    # convert into GET request and show view again
    request.method = 'GET'
    request.POST = QueryDict()

    # call the original view but set response status to forbidden
    response = _csrf_failed_view.callback(request, *_csrf_failed_view.args, **_csrf_failed_view.kwargs)
    if response.status_code == 200:
        response.status_code = 403
    return response


def default_csrf_behaviour(view):
    """
    View decorator to cause CSRF middleware to behave in Django's standard
    fashion, i.e. if not exempt and failing, present Django's error page
    rather than the original view
    """
    view.no_moj_csrf = True
    return view


class CsrfViewMiddleware(DjangoCsrfViewMiddleware):
    """
    Augments Django CSRF middleware to present the same failed view by turning the POST
    request into a GET and showing a sensible error message

    Usage:

    * Replace django.middleware.csrf.CsrfViewMiddleware with mtp_common.auth.csrf.CsrfViewMiddleware
      in `settings.MIDDLEWARE`
    * Add `CSRF_FAILURE_VIEW = 'mtp_common.auth.csrf.csrf_failure'` to `settings`
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        _csrf_failed_view.no_moj_csrf = getattr(callback, 'no_moj_csrf', False)
        _csrf_failed_view.callback = callback
        _csrf_failed_view.args = callback_args
        _csrf_failed_view.kwargs = callback_kwargs
        return super().process_view(request, callback, callback_args, callback_kwargs)
