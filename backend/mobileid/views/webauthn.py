from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from mobileid.forms.UserRegisterForm import UserRegisterForm

def register(request):
    if request.method == "POST":
        # Bind both form fields and uploaded files
        form = UserRegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()
            login(request, user)                     # Auto-login after sign-up
            messages.success(request, "Registration successful!")
            return redirect("dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, "registration/register.html", {"form": form})