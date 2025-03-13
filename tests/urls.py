from django.http import HttpResponse
from django.template import RequestContext, Template
from django.urls import include, reverse_lazy, re_path

from mtp_common.auth import views
from mtp_common.auth.basic import basic_auth
from mtp_common.metrics.views import metrics_view
from mtp_common.user_admin.forms import SignUpForm
import mtp_common.user_admin.views as user_admin_views
from mtp_common.views import SettingsView


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
    re_path(r'^dummy$', dummy_view, name='dummy'),

    re_path(r'^feedback/$', lambda request: HttpResponse('FEEDBACK'), name='submit_ticket'),

    # authentication views
    re_path(r'^login/$', views.login, {
        'template_name': 'login.html',
    }, name='login'),
    re_path(
        r'^logout/$', views.logout, {
            'template_name': 'login.html',
            'next_page': 'dummy',
        }, name='logout'
    ),
    re_path(
        r'^password_change/$', views.password_change, {
            'template_name': 'mtp_common/auth/password_change.html',
        }, name='password_change'
    ),
    re_path(
        r'^password_change_done/$', views.password_change_done, {
            'template_name': 'mtp_common/auth/password_change_done.html',
        }, name='password_change_done'
    ),
    re_path(
        r'^reset-password/$', views.reset_password, {
            'template_name': 'mtp_common/auth/reset-password.html',
        }, name='reset_password'
    ),
    re_path(
        r'^reset-password/$', views.reset_password_done, {
            'template_name': 'mtp_common/auth/reset-password-done.html',
        }, name='reset_password_done'
    ),
    re_path(
        r'^email_change/$', views.email_change, {
            'cancel_url': reverse_lazy('settings'),
        }, name='email_change'
    ),

    # unauthenticated user views
    re_path(r'^users/sign-up/$', user_admin_views.SignUpView.as_view(form_class=TestingSignUpForm), name='sign-up'),

    # user account administration
    re_path(r'^settings$', SettingsView.as_view(), name='settings'),
    re_path(r'^user-admin/', include('mtp_common.user_admin.urls')),
    re_path(
        r'^users/request/(?P<account_request>\d+)/accept/$',
        user_admin_views.AcceptRequestView.as_view(),
        name='accept-request'
    ),

    # mocked basic auth view
    re_path(r'^basic-auth/', basic_auth('BASIC_USER', 'BASIC_PASSWORD')(dummy_view), name='basic-auth'),

    # prometheus metrics
    re_path(r'^metrics.txt$', metrics_view, name='prometheus_metrics'),
]
