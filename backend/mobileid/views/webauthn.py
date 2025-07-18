from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

# import forms
from mobileid.forms.WebAuthnForms import UserLoginForm, UserRegisterForm


def web_register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("mobileid:web_index")
        messages.error(request, "Please correct the highlighted errors.")
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
                return redirect('mobileid:web_index')
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = UserLoginForm()

    return render(request, 'webauthn/login.html', {'form': form})


@login_required(login_url="login")
def web_logout(request):
    logout(request)
    return redirect("mobileid:web_login")
