from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from mobileid.models import UserBarcodeSettings, UserProfile


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

    if request.user.useraccount.account_type == "School":
        return render(request, "index/index.html", context)

    return render(request, "index/index_user.html", context)
