from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from mobileid.models import StudentInformation


@login_required(login_url='/login/')
def index(request):
    try:
        user_profile = StudentInformation.objects.get(user=request.user)
        student_id = user_profile.student_id
        name = user_profile.name
    except StudentInformation.DoesNotExist:
        return redirect('setup')

    return render(request, 'index.html', {'student_id': student_id, 'name': name, })



