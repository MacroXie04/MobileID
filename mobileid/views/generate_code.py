from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from mobileid.models import StudentInformation, UserBarcodeSettings
from mobileid.project_code import send_code, barcode


# Generate Barcode
@csrf_exempt
@login_required(login_url='/login/')
def generate_code(request):
    # request user information and settings from the database
    user_profile = StudentInformation.objects.get(user=request.user)
    user_settings = UserBarcodeSettings.objects.get(user=request.user)
    user_session = user_profile.session

    # using static barcode
    if user_settings.barcode_status:
        web_barcode = user_settings.static_barcode
        response_data = {
            "status": "success",
            "barcode_type": "static",
            "content": "static code",
            "barcode": web_barcode,
        }
        return JsonResponse(response_data)

    # using dynamic barcode
    else:
        print('using dynamic barcode')
        # using dynamic barcode with server verification
        if user_settings.server_verification:
            print('using server verification')
            if not user_session:
                web_barcode = ''
                response_data = {
                    "status": "failure",
                    "barcode_type": "dynamic",
                    "content": "no session data",
                    "barcode": web_barcode,
                }
                return JsonResponse(response_data, status=200)

            else:
                if not user_profile.mobile_id_rand_array:
                    try:
                        server_result = barcode.uc_merced_mobile_id(user_session)
                        user_profile.current_mobile_id_rand = 0
                        user_profile.mobile_id_rand_array = server_result['mobile_id_rand_array']
                        user_profile.barcode = server_result['barcode']
                        user_profile.code_student_id = server_result['student_id']
                        user_profile.save()
                    except Exception:
                        web_barcode = ''
                        response_data = {
                            "status": "failure",
                            "barcode_type": "dynamic",
                            "content": "no session error",
                            "barcode": web_barcode,
                        }
                        return JsonResponse(response_data, status=200)

                max_retries = 11
                attempt = 0

                while attempt < max_retries:
                    if user_profile.current_mobile_id_rand >= len(user_profile.mobile_id_rand_array):
                        try:
                            server_result = barcode.uc_merced_mobile_id(user_session)
                            user_profile.current_mobile_id_rand = 0
                            user_profile.mobile_id_rand_array = server_result['mobile_id_rand_array']
                            user_profile.barcode = server_result['barcode']
                            user_profile.code_student_id = server_result['student_id']
                            user_profile.save()
                        except Exception:
                            web_barcode = ''
                            response_data = {
                                "status": "failure",
                                "barcode_type": "dynamic",
                                "content": "session data error",
                                "barcode": web_barcode,
                            }
                            return JsonResponse(response_data, status=200)

                    # Generate the timestamp from the backend
                    california_tz = pytz.timezone('America/Los_Angeles')
                    now = datetime.now(california_tz)
                    timestamp = now.strftime('%Y%m%d%H%M%S')

                    current = user_profile.mobile_id_rand_array[user_profile.current_mobile_id_rand]
                    print(f'trying to send code: {current}')
                    send_code_result = send_code.send_otc(current, user_profile.code_student_id, user_profile.barcode)
                    if send_code_result.get("status") == "success":
                        web_barcode = str(timestamp) + str(user_profile.barcode)
                        response_data = {
                            "status": "success",
                            "barcode_type": "dynamic",
                            "content": f"{current} - added",
                            "barcode": web_barcode,
                        }
                        return JsonResponse(response_data, status=200)

                    attempt += 1
                    user_profile.current_mobile_id_rand += 1
                    user_profile.save()

        # using dynamic barcode without server verification
        else:
            print('not using server verification')

            if user_profile.barcode:
                # Generate the timestamp from the backend
                california_tz = pytz.timezone('America/Los_Angeles')
                now = datetime.now(california_tz)
                timestamp = now.strftime('%Y%m%d%H%M%S')

                web_barcode = str(timestamp) + str(user_profile.barcode)
                response_data = {
                    "status": "success",
                    "barcode_type": "dynamic",
                    "content": "server verification disabled",
                    "barcode": web_barcode,
                }
                return JsonResponse(response_data, status=200)

            else:
                try:
                    print(user_session)
                    server_result = barcode.uc_merced_mobile_id(user_session)
                    print('server_result', server_result)
                    user_profile.barcode = server_result['barcode']
                    user_profile.code_student_id = server_result['student_id']
                    user_profile.save()
                except Exception as e:
                    print(e)
                    web_barcode = ''
                    response_data = {
                        "status": "failure",
                        "barcode_type": "static",
                        "content": "session error",
                        "barcode": web_barcode,
                    }
                    return JsonResponse(response_data, status=200)

                california_tz = pytz.timezone('America/Los_Angeles')
                now = datetime.now(california_tz)
                timestamp = now.strftime('%Y%m%d%H%M%S')

                web_barcode = str(timestamp) + str(user_profile.barcode)
                response_data = {
                    "status": "success",
                    "barcode_type": "dynamic",
                    "content": "server verification disabled",
                    "barcode": web_barcode,
                }
                return JsonResponse(response_data, status=200)
