from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import RequestContext, Template

from mtp_common.auth import views
from mtp_common.auth.basic import basic_auth
from mtp_common.user_admin.forms import SignUpForm
import mtp_common.user_admin.views as user_admin_views


def mocked_template():
    # mock this function in tests
    return 'DUMMY'


def mocked_context(request):
    # mock this function in tests
    return {}


def dummy_view(request):
    content = Template(mocked_template()).render(RequestContext(request, mocked_context(request)))
    return HttpResponse(content=content)


class TestingSignUpForm(SignUpForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        role_field = self.fields['role']
        role_field.initial = 'general'
        role_field.choices = (('general', 'General role'), ('special', 'Special role'))


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

    # unauthenticated user views
    url(r'^users/sign-up/$', user_admin_views.SignUpView.as_view(form_class=TestingSignUpForm), name='sign-up'),

    # user account administration
    url(r'^settings$', login_required(lambda request: HttpResponse('SETTINGS')), name='settings'),
    url(r'^user-admin/', include('mtp_common.user_admin.urls')),
    url(
        r'^users/request/(?P<account_request>\d+)/accept/$',
        user_admin_views.AcceptRequestView.as_view(),
        name='accept-request'
    ),

    # mocked basic auth view
    url(r'^basic-auth/', basic_auth('BASIC_USER', 'BASIC_PASSWORD')(dummy_view), name='basic-auth')
]
