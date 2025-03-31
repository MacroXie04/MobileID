from mobileid.forms.SetupForm import SetupForm
from django.shortcuts import redirect
from django.shortcuts import render
from mobileid.models import StudentInformation
from django.contrib.auth.decorators import login_required
from mobileid.models import UserBarcodeSettings
from mobileid.forms.UserBarcodeSettingsForm import UserBarcodeSettingsForm


@login_required(login_url='/login/')
def setup(request):
    user_profile, created = StudentInformation.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = SetupForm(request.POST, request.FILES)  # 注意这里
        if form.is_valid():
            data = form.cleaned_data
            user_profile.name = data.get('name')
            user_profile.student_id = data.get('student_id')

            if 'avatar' in request.FILES:
                user_profile.avatar = request.FILES['avatar']

            # process the session data
            if user_profile.session != data.get('session'):
                user_profile.mobile_id_rand_array = []
                user_profile.current_mobile_id_rand = 0
                user_profile.barcode = ""
                user_profile.code_student_id = ""

            if data.get('session'):
                user_profile.session = data.get('session')
            user_profile.save()
            return redirect('index')
    else:
        form = SetupForm(initial={
            'name': user_profile.name,
            'student_id': user_profile.student_id,
            'Session': user_profile.session,
        })

    return render(request, 'setup.html', {'form': form})



@login_required
def settings(request):
    settings, created = UserBarcodeSettings.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UserBarcodeSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('index')  # 修改为你实际的路由名
    else:
        form = UserBarcodeSettingsForm(instance=settings)

    return render(request, 'settings.html', {'form': form})
