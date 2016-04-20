from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^users/$', views.list_users, name='list-users'),
    url(r'^users/new/$', views.UserCreationView.as_view(), name='new-user'),
    url(r'^users/(?P<username>[\w-]+)/edit/$', views.UserUpdateView.as_view(), name='edit-user'),
    url(r'^users/(?P<username>[\w-]+)/delete/$', views.delete_user, name='delete-user'),
]
