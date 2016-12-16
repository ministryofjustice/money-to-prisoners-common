from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^users/$', views.list_users, name='list-users'),
    url(r'^users/new/$', views.UserCreationView.as_view(), name='new-user'),
    url(r'^users/(?P<username>[^/]+)/edit/$', views.UserUpdateView.as_view(), name='edit-user'),
    url(r'^users/(?P<username>[^/]+)/delete/$', views.delete_user, name='delete-user'),
    url(r'^users/(?P<username>[^/]+)/undelete/$', views.undelete_user, name='undelete-user'),
    url(r'^users/(?P<username>[^/]+)/unlock/$', views.unlock_user, name='unlock-user'),
]
