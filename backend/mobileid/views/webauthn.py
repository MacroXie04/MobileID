from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.contrib.auth import (
    login,
    authenticate,
    logout
)

# import forms
from mobileid.forms.WebAuthnForms import (
    UserRegisterForm,
    UserLoginForm,
)

def web_register(request):
    if request.method == "POST":
        # Bind both form fields and uploaded files
        form = UserRegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, "webauthn/register.html", {"form": form})


def web_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = UserLoginForm()

    return render(request, 'webauthn/login.html', {'form': form})


@login_required(login_url='login')
def web_logout(request):
    logout(request)
    return redirect('')
