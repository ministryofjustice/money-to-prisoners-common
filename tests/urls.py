from django.conf.urls import include, url
from django.http import HttpResponse
from django.template import RequestContext, Template

from mtp_common.auth import views


def mocked_template():
    # mock this function in tests
    return 'DUMMY'


def mocked_context(request):
    # mock this function in tests
    return {}


def dummy_view(request):
    content = Template(mocked_template()).render(RequestContext(request, mocked_context(request)))
    return HttpResponse(content=content)


urlpatterns = [
    # dummy/mocked template
    url(r'^dummy$', dummy_view, name='dummy'),

    url(r'^feedback/$', lambda request: HttpResponse('FEEDBACK'), name='submit_ticket'),

    # authentication views
    url(r'^login/$', views.login, {
        'template_name': 'login.html',
    }, name='login'),
    url(
        r'^logout/$', views.logout, {
            'template_name': 'login.html',
            'next_page': 'dummy',
        }, name='logout'
    ),
    url(
        r'^password_change/$', views.password_change, {
            'template_name': 'mtp_common/auth/password_change.html',
        }, name='password_change'
    ),
    url(
        r'^password_change_done/$', views.password_change_done, {
            'template_name': 'mtp_common/auth/password_change_done.html',
        }, name='password_change_done'
    ),
    url(
        r'^reset-password/$', views.reset_password, {
            'template_name': 'mtp_common/auth/reset-password.html',
        }, name='reset_password'
    ),
    url(
        r'^reset-password/$', views.reset_password_done, {
            'template_name': 'mtp_common/auth/reset-password-done.html',
        }, name='reset_password_done'
    ),

    # user account administration
    url(r'^user-admin/', include('mtp_common.user_admin.urls')),
]
