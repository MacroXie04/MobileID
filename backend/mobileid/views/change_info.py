# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from mobileid.forms.InfoForm import (
    StudentInformationUpdateForm,
    UserBarcodeSettingsForm,
)
from mobileid.models import (
    StudentInformation,
    UserBarcodeSettings,
)

@login_required(login_url='/login')
def edit_profile(request):
    # Ensure the student info record exists
    student_info, _ = StudentInformation.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = StudentInformationUpdateForm(
            request.POST,
            request.FILES,
            instance=student_info
        )
        if form.is_valid():
            form.save()
            return redirect('mobileid:index')  # Redirect to index after successful update
    else:
        form = StudentInformationUpdateForm(instance=student_info)

    context = {
        'form': form,
        'student_info': student_info,
    }
    return render(request, 'index/profile_edit.html', context)


@login_required(login_url='/login')
def edit_barcode_settings(request):
    """
    Allow the logged‑in user to configure their personal barcode behaviour.

    * If `barcode_pull` is checked, the form validation will force `barcode` to be empty.
    * The form scopes available barcodes to those owned by the current user.
    """
    settings_obj, _ = UserBarcodeSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserBarcodeSettingsForm(
            request.POST,
            instance=settings_obj,
            user=request.user
        )
        if form.is_valid():
            form.save()
            return redirect('mobileid:index')
    else:
        form = UserBarcodeSettingsForm(
            instance=settings_obj,
            user=request.user
        )

    context = {
        'form': form,
        'settings': settings_obj,
    }
    return render(request, 'index/settings_edit.html', context)


