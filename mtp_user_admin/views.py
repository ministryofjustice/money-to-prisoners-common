from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

from moj_auth import api_client


@login_required
def list_users(request):
    users = api_client.get_connection(request).users.get()['results']
    return render_to_response('mtp_user_admin/list.html', {'users': users})
