import random
from datetime import datetime, timedelta
import pytz
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mobileid.models import StudentInformation, UserBarcodeSettings, Barcode
from mobileid.project_code import barcode


# Generate Barcode
@csrf_exempt
@login_required(login_url='/login/')
def generate_code(request):
    # Retrieve user profile and settings with error handling
    try:
        user_settings = UserBarcodeSettings.objects.get(user=request.user)
    except (StudentInformation.DoesNotExist, UserBarcodeSettings.DoesNotExist):
        return JsonResponse({"status": "error", "message": "User settings not found."})

    # Decide which barcode to use
    # If the user does not have a barcode in their settings, automatically enable barcode_pull
    auto_enabled = False
    if not user_settings.barcode_pull and user_settings.barcode is None:
        user_settings.barcode_pull = True
        user_settings.save()
        auto_enabled = True

    if user_settings.barcode_pull:
        total = Barcode.objects.count()
        if total == 0:
            return JsonResponse({"status": "error", "message": "No barcode available."})
        random_index = random.randint(0, total - 1)
        code = Barcode.objects.all()[random_index]
    else:
        code = user_settings.barcode

    # Set up timezone and current time
    california_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(california_tz)

    # Extra info message if barcode_pull was auto-enabled
    extra_info = " (Auto-enabled barcode_pull)" if auto_enabled else ""

    # Helper function to update barcode usage
    def update_usage(barcode_obj):
        barcode_obj.total_usage += 1
        barcode_obj.last_used = datetime.now(california_tz)
        barcode_obj.save()

    # Dynamic barcode generation branch
    if user_settings.dynamic_barcode:
        # Generate timestamp
        if user_settings.timestamp_verification:
            timestamp = current_time.strftime('%Y%m%d%H%M%S')
        else:
            start_date = current_time - timedelta(days=365)
            random_seconds = random.randint(0, int((current_time - start_date).total_seconds()))
            random_datetime = start_date + timedelta(seconds=random_seconds)
            timestamp = random_datetime.strftime('%Y%m%d%H%M%S')

        # Server verification branch
        if user_settings.server_verification:
            try:
                # Use the session from user's assigned barcode
                session = user_settings.barcode.session
                server_result = barcode.auto_send_code(session)
                if server_result.get('success'):
                    content_msg = f"code {server_result.get('code')} verified"
                else:
                    content_msg = f"server verification failed - {code.barcode[-4:]}"
                update_usage(code)
                return JsonResponse({
                    "status": "success",
                    "barcode_type": "dynamic code",
                    "content": f"{content_msg}{extra_info}",
                    "barcode": f"{timestamp}{code.barcode}",
                })
            except Exception as e:
                return JsonResponse({
                    "status": "success",
                    "barcode_type": "dynamic code",
                    "content": f"server verification failed - {code.barcode[-4:]}{extra_info}",
                    "barcode": f"{timestamp}{code.barcode}",
                })
        else:
            update_usage(code)
            return JsonResponse({
                "status": "success",
                "barcode_type": "dynamic code",
                "content": f"dynamic code - {code.barcode[-4:]}{extra_info}",
                "barcode": f"{timestamp}{code.barcode}",
            })
    else:
        # Static barcode branch
        update_usage(code)
        return JsonResponse({
            "status": "success",
            "barcode_type": "static",
            "content": f"static code - {code.barcode[-4:]}{extra_info}",
            "barcode": code.barcode,
        })
