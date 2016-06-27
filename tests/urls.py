from django.conf.urls import include, url
from django.shortcuts import render

from mtp_common.auth import views


def get_context():
    # mock this function in tests
    return {}


def dummy_view(request):
    return render(request, 'dummy', context=get_context())


urlpatterns = [
    # dummy/mocked template
    url(r'^dummy$', dummy_view, name='dummy'),

    # authentication views
    url(r'^login/$', views.login, {
        'template_name': 'login.html',
    }, name='login'),
    url(
        r'^logout/$', views.logout, {
            'template_name': 'logout.html',
            'next_page': 'dummy',
        }, name='logout'
    ),
    url(
        r'^password_change/$', views.password_change, {
            'template_name': 'login.html',
        }, name='password_change'
    ),
    url(
        r'^password_change_done/$', views.password_change_done, {
            'template_name': 'done.html',
        }, name='password_change_done'
    ),
    url(
        r'^reset-password/$', views.reset_password, {
            'template_name': 'dummy.html',
        }, name='reset_password'
    ),
    url(
        r'^reset-password/$', views.reset_password_done, {
            'template_name': 'dummy.html',
        }, name='reset_password_done'
    ),

    # user account administration
    url(r'^user-admin/', include('mtp_common.user_admin.urls')),
]
