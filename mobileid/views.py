from .forms import UserLoginForm, UserRegisterForm
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import StudentInformation
from django.http import HttpResponse
from .project_code import send_code, barcode
from django.views.decorators.http import require_POST
from django.http import JsonResponse

@login_required(login_url='/login/')
def index(request):
    try:
        user_profile = StudentInformation.objects.get(user=request.user)
        student_id = user_profile.student_id
        name = user_profile.name
    except StudentInformation.DoesNotExist:
        return redirect('/settings/')

    return render(request, 'index.html', {'student_id': student_id, 'name': name,})


@login_required(login_url='/login/')
def settings(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        student_id = request.POST.get('student_id')
        section = request.POST.get('section')

        # Update the user profile
        user_profile, created = StudentInformation.objects.get_or_create(user=request.user)
        user_profile.name = name
        user_profile.student_id = student_id
        user_profile.section = section
        user_profile.save()

        return redirect('index')
    return render(request, 'settings.html')


@login_required(login_url='/login/')
def logout(request):
    logout(request)
    return redirect('login')


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserRegisterForm()

    return render(request, 'register.html', {'form': form})

def user_login(request):
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

    return render(request, 'login.html', {'form': form})

# Generate Barcode
@require_POST
@login_required(login_url='/login/')
def generate_code(request):
    user_profile = StudentInformation.objects.get(user=request.user)
    section = user_profile.section

    if not section:
        return redirect('index')

    # 如果没有随机数组则先初始化
    if not user_profile.mobile_id_rand_array:
        try:
            result = barcode.uc_merced_mobile_id(section)
            user_profile.current_mobile_id_rand = 0
            user_profile.mobile_id_rand_array = result['mobile_id_rand_array']
            user_profile.barcode = result['barcode']
            user_profile.code_student_id = result['student_id']
            user_profile.save()
        except Exception as e:
            return HttpResponse("Invalid cookie data", status=400)

    max_retries = 3
    attempt = 0

    while attempt < max_retries:
        if user_profile.current_mobile_id_rand >= len(user_profile.mobile_id_rand_array):
            try:
                result = barcode.uc_merced_mobile_id(section)
                user_profile.current_mobile_id_rand = 0
                user_profile.mobile_id_rand_array = result['mobile_id_rand_array']
                user_profile.barcode = result['barcode']
                user_profile.code_student_id = result['student_id']
                user_profile.save()
            except Exception as e:
                return HttpResponse("Failed to update mobile id array", status=400)

        current = user_profile.mobile_id_rand_array[user_profile.current_mobile_id_rand]
        send_code_result = send_code.send_otc(current, user_profile.code_student_id, user_profile.barcode)
        if send_code_result.get("status") == "success":
            response_data = {
                "status": "success",
                "student_id": user_profile.code_student_id,
                "code": current,
                "response": send_code_result.get("response")
            }
            return JsonResponse(response_data)
        attempt += 1
        user_profile.current_mobile_id_rand += 1
        user_profile.save()

    return HttpResponse("Failed: code {} response: {}".format(
        current, send_code_result.get("response")), status=400)