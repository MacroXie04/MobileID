import json
import random

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from mobileid.forms.TransferCodeForm import TransferCodeForm
from mobileid.models import StudentInformation, Transfer


@csrf_exempt
def transfer_key(request):
    if request.method == "POST":
        try:
            # decode the json data
            data = json.loads(request.body)
            cookie = data.get("cookie")
            if not cookie:
                return JsonResponse({"error": "No cookie Data Found"}, status=400)

            # generate a unique 6-digit code
            unique_code = None
            while True:
                candidate = str(random.randint(100000, 999999))
                if not Transfer.objects.filter(unique_code=candidate).exists():
                    unique_code = candidate
                    break

            # save to the database
            transfer_obj = Transfer.objects.create(cookie=cookie, unique_code=unique_code)
            transfer_obj.save()

            # return the unique code
            return JsonResponse({"unique_code": unique_code})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Please sent request with script"}, status=405)


@login_required(login_url='/login/')
def transfer_code(request):
    if request.method == "POST":
        form = TransferCodeForm(request.POST)
        if form.is_valid():
            transfer_code = form.cleaned_data['transfer_code']
            try:
                transfer_obj = Transfer.objects.get(unique_code=transfer_code)
            except Transfer.DoesNotExist:
                form.add_error('transfer_code', "TransferCode is not valid.")
                return render(request, "transfer.html", {'form': form})
            try:
                user_profile = StudentInformation.objects.get(user=request.user)
            except StudentInformation.DoesNotExist:
                return redirect("settings")
            user_profile.session = transfer_obj.cookie
            user_profile.save()
            transfer_obj.delete()
            return redirect("index")
        else:
            return render(request, "transfer.html", {'form': form})
    else:
        form = TransferCodeForm()
    return render(request, "transfer.html", {'form': form})
