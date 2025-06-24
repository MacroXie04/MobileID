from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from mobileid.models import (
    StudentInformation,
    UserBarcodeSettings
)

@login_required(login_url='/login')
def index(request):
    try:
        info = StudentInformation.objects.get(user=request.user)
    except StudentInformation.DoesNotExist:
        return redirect("mobileid:web_register")

    context = {
        "name": info.name,
        "student_id": info.student_id,
        "user_profile_img": info.user_profile_img,
    }

    return render(request, "index/index.html", context)