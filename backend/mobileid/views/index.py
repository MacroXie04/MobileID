from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from mobileid.models import UserProfile, UserBarcodeSettings


@login_required(login_url="/login")
def index(request):
    try:
        info = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect("mobileid:web_edit_profile")

    context = {
        "name": info.name,
        "information_id": info.information_id,
        "user_profile_img": info.user_profile_img,
    }

    return render(request, "index/index.html", context)
