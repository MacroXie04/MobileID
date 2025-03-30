import json
import random
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from mobileid.models import StudentInformation, Transfer


@csrf_exempt
def transfer_key(request):
    if request.method == "POST":
        try:
            # 解析 JSON 数据
            data = json.loads(request.body)
            cookie = data.get("cookie")
            if not cookie:
                return JsonResponse({"error": "No cookie Data Found"}, status=400)

            # 生成一个唯一的6位数字（避免重复）
            unique_code = None
            while True:
                candidate = str(random.randint(100000, 999999))
                if not Transfer.objects.filter(unique_code=candidate).exists():
                    unique_code = candidate
                    break

            # 将 cookie 与生成的唯一码存入数据库
            transfer_obj = Transfer.objects.create(cookie=cookie, unique_code=unique_code)
            transfer_obj.save()

            # 返回生成的唯一6位数字
            return JsonResponse({"unique_code": unique_code})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Please sent request with script"}, status=405)


@login_required(login_url='/login/')
def transfer_code(request):
    if request.method == "POST":
        user_profile = StudentInformation.objects.get(user=request.user)

        transfer_code = request.POST.get("transfer_code", "").strip()
        if not transfer_code or len(transfer_code) != 6 or not transfer_code.isdigit():
            messages = [f"TransferCode is not valid."]
            return render(request, "transfer.html", {'messages': messages})

        try:
            transfer_obj = Transfer.objects.get(unique_code=transfer_code)
        except Transfer.DoesNotExist:
            messages = [f"TransferCode is not valid."]
            return render(request, "transfer.html", {'messages': messages})

        cookie_value = transfer_obj.cookie

        try:
            user_profile = StudentInformation.objects.get(user=request.user)
        except StudentInformation.DoesNotExist:
            return redirect("settings")

        user_profile.section = cookie_value
        user_profile.save()

        transfer_obj.delete()

        return redirect("index")
    else:
        return render(request, "transfer.html")
