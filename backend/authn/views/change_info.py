from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from mobileid.forms.InfoForm import (InformationUpdateForm)
from authn.models import UserProfile


@login_required
def edit_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = InformationUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("mobileid:web_index")
    else:
        # Pre-load current avatar into hidden Base64 field
        form = InformationUpdateForm(
            instance=profile,
            initial={"user_profile_img_base64": profile.user_profile_img},
        )

    return render(request, "../../authn/templates/manage/profile_edit.html", {"form": form, "profile": profile})
