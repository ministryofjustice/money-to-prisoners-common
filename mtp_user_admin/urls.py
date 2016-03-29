from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^users/$', views.list_users, name='list-users'),
    url(r'^users/(?P<username>[\w-]+)/delete/$', views.delete_user, name='delete-user'),
]
