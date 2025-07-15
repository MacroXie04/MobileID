from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url="mobileid:web_login")
def account_disabled(request):
    user_info = {
        'user_name': request.user.username,
        'information_id': request.user.userprofile.information_id,
    }
    return render(request, "account_disabled.html", user_info)
