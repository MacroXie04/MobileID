from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url="mobileid:web_login")
def account_disabled(request):
    return render(request, "account_disabled.html")
