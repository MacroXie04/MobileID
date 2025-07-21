from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def index(request):
    # Redirect call back function
    return redirect("mobileid:web_login")