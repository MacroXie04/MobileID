import json
import random
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from mobileid.models import StudentInformation, Transfer
from django.views.decorators.http import require_GET, require_POST


@require_POST
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
