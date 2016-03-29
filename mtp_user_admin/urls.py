from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^users/$', views.list_users, name='list-users'),
]
