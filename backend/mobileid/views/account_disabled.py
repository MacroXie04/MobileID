from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url='mobileid:web_login')
def account_disabled(request):
    return render(request, 'account_disabled.html') 