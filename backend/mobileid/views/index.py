from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from mobileid.models import UserProfile, UserAccount


@login_required(login_url="/login")
def index(request):
    # load user profile
    try:
        info = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect("mobileid:web_edit_profile")

    context = {
        "name": info.name,
        "information_id": info.information_id,
        "user_profile_img": info.user_profile_img,
    }

    user_account_type = request.user.useraccount.account_type
    # TODO: handle account with out user account settings


    if user_account_type == "School":
        return render(request, "index/index.html", context)
    elif user_account_type == "User":
        return render(request, "index/index_user.html", context)
    else:
        return render(request, "index/index_user.html", context)
