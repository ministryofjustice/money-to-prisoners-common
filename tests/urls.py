from django.conf.urls import url
from django.shortcuts import render


def get_context():
    # mock this function in tests
    return {}


def dummy_view(request):
    return render(request, 'dummy', context=get_context())


urlpatterns = [
    url(r'^dummy$', dummy_view, name='dummy')
]
