from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from mobileid.models import (
    UserProfile,
    UserBarcodeSettings
)

@login_required(login_url='/login')
def index(request):
    try:
        info = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect("mobileid:web_register")

    context = {
        "name": info.name,
        "id": info.id,
        "user_profile_img": info.user_profile_img,
    }

    return render(request, "index/index.html", context)