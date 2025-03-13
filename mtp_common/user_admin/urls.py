from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^users/$', views.UserListView.as_view(), name='list-users'),

    re_path(r'^users/new/$', views.UserCreationView.as_view(), name='new-user'),

    re_path(r'^users/(?P<username>[^/]+)/edit/$', views.UserUpdateView.as_view(), name='edit-user'),
    re_path(r'^users/(?P<username>[^/]+)/delete/$', views.delete_user, name='delete-user'),
    re_path(r'^users/(?P<username>[^/]+)/undelete/$', views.undelete_user, name='undelete-user'),
    re_path(r'^users/(?P<username>[^/]+)/unlock/$', views.unlock_user, name='unlock-user'),

    # accept-request view should be subclassed by clients
    re_path(r'^users/request/(?P<account_request>\d+)/decline/$', views.decline_request, name='decline-request'),
]
