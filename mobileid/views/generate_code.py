import random
from datetime import datetime, timedelta

import pytz
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from mobileid.models import StudentInformation, UserBarcodeSettings, Barcode
from mobileid.project_code.barcode import auto_send_code


# Generate Barcode
@login_required(login_url='/login/')
def generate_code(request):
    # Retrieve user profile and settings with error handling
    try:
        user_settings = UserBarcodeSettings.objects.get(user=request.user)
    except (StudentInformation.DoesNotExist, UserBarcodeSettings.DoesNotExist):
        return JsonResponse({"status": "error", "message": "User settings not found."})

    # ---------------------------------------------
    # init the barcode and message information
    # ---------------------------------------------
    california_tz = pytz.timezone('America/Los_Angeles')

    if user_settings.barcode_pull:
        # give user a barcode based on each barcode usage
        queryset = Barcode.objects.all().order_by('last_used', 'total_usage')
        if queryset.exists():
            user_barcode = queryset.first()
        else:
            return JsonResponse({"status": "error", "message": "No barcodes available."})
    else:
        # use thr barcode assigned to the user
        try:
            # init the barcode
            user_barcode = user_settings.barcode
        except Barcode.DoesNotExist:
            return JsonResponse({"status": "error", "message": "No barcode assigned to user."})

    # ---------------------------------------------
    # Helper function to update barcode usage
    # ---------------------------------------------
    def update_usage(obj):
        obj.total_usage += 1
        obj.last_used = datetime.now(california_tz)
        obj.save()

    # ---------------------------------------------
    # process the static barcode
    # ---------------------------------------------
    if user_barcode.barcode_type.lower() == "static":
        # update the usage
        update_usage(user_barcode)

        # response the barcode
        return JsonResponse({
            "status": "success",
            "barcode_type": f"static",
            "content": f"Static: Ending with {user_barcode.barcode[-4:]}",
            "barcode": f"{user_barcode.barcode}",
        })

    # ---------------------------------------------
    # process the dynamic barcode
    # ---------------------------------------------
    elif user_barcode.barcode_type.lower() == "dynamic":
        # get the session information
        user_session = user_barcode.session
        extra_info = f'Dynamic: Ending with {user_barcode.barcode[-4:]}'

        # init the timestamp
        if user_settings.timestamp_verification:
            # Set up timezone and current time
            current_time = datetime.now(california_tz)
            time_stamp = current_time.strftime('%Y%m%d%H%M%S')
        else:
            start_date = datetime.now() - timedelta(days=365)
            random_seconds = random.randint(0, int((datetime.now() - start_date).total_seconds()))
            random_datetime = start_date + timedelta(seconds=random_seconds)
            time_stamp = random_datetime.strftime('%Y%m%d%H%M%S')

        # student id server verification
        if user_settings.server_verification and not user_settings.barcode_pull:

            # check session
            if not user_session:
                content_msg = "Session is missing "

            else:
                try:
                    server_result = auto_send_code(user_session)
                    if server_result["status"] == "success":
                        content_msg = f"Server Verification Success: {server_result['code']} "
                    else:
                        content_msg = "Server Verification Failed "
                        user_barcode.session = None
                        user_barcode.save()

                except Exception as e:
                    content_msg = "Server Verification Error "

        else:
            # no server verification
            content_msg = ""

        update_usage(user_barcode)

        # response the barcode
        return JsonResponse({
            "status": "success",
            "barcode_type": f"dynamic",
            "content": f"{content_msg}{extra_info}",
            "barcode": f"{time_stamp}{user_barcode.barcode}",
        })

    else:
        return JsonResponse({
            "status": "error",
            "message": "Invalid barcode type."
        })
