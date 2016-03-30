from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.shortcuts import render
from slumber.exceptions import HttpNotFoundError

from moj_auth import api_client
from mtp_utils.api import retrieve_all_pages


@login_required
@permission_required('auth.change_user', raise_exception=True)
def list_users(request):
    users = retrieve_all_pages(
        api_client.get_connection(request).users.get
    )
    return render(request, 'mtp_user_admin/list.html', {'users': users})


@login_required
@permission_required('auth.delete_user', raise_exception=True)
def delete_user(request, username):
    if request.method == 'POST':
        try:
            api_client.get_connection(request).users(username).delete()
            return render(request, 'mtp_user_admin/deleted.html', {'username': username})
        except HttpNotFoundError:
            raise Http404
    else:
        return render(request, 'mtp_user_admin/delete.html', {'username': username})
