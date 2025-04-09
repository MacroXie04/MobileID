from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from mobileid.models import StudentInformation, UserBarcodeSettings


@login_required(login_url='/login/')
def index(request):
    # make sure the user has a profile and setting before accessing the index page
    try:
        user_profile = StudentInformation.objects.get(user=request.user)
        user_settings = UserBarcodeSettings.objects.get(user=request.user)
        student_id = user_profile.student_id
        name = user_profile.name
    except StudentInformation.DoesNotExist:
        return redirect('setup')
    except UserBarcodeSettings.DoesNotExist:
        return redirect('settings')


    return render(request, 'index.html', {
        'student_id': student_id,
        'name': name,
        'user_profile': user_profile
    })
