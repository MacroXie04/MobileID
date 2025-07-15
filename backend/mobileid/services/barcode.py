import random
import time
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from mobileid.models import UserBarcodeSettings, Barcode, UserAccount, BarcodeUsage
from mobileid.project_code.barcode import auto_send_code
from barcode.settings import PACIFIC_TZ, SELENIUM_ENABLED



def generate_unique_identification_barcode():
    while True:
        code = ''.join([str(random.randint(0, 9)) for _ in range(28)])
        if not Barcode.objects.filter(barcode=code).exists():
            return code


def update_user_identification_barcode(user):
    user_identification_barcode = Barcode.objects.filter(
        user=user, barcode_type="Identification"
    )


def get_dynamic_barcode():

    # select all dynamic barcodes
    available_barcodes = Barcode.objects.filter(barcode_type="DynamicBarcode")
    # join BarcodeUsage, sort by total_usage and last_used
    barcode_with_usage = BarcodeUsage.objects.filter(
        barcode__in=available_barcodes
    ).order_by('total_usage', 'last_used').select_related('barcode')

    if barcode_with_usage.exists():
        selected_usage = barcode_with_usage.first()
        selected_barcode = selected_usage.barcode
        # update usage record after allocation
        selected_usage.total_usage = selected_usage.total_usage + 1
        selected_usage.save()
        return selected_barcode
    else:
        return None


@transaction.atomic
def generate_barcode(user):
    # load user settings and account type
    try:
        user_account = UserAccount.objects.get(user=user)
    except UserBarcodeSettings.DoesNotExist:
        user_identification_barcode = Barcode.objects.create(
            user=user,
            barcode_type="Identification",
            barcode=None,
        )

        user_settings = UserBarcodeSettings.objects.create(
            user=user,
            barcode=user_identification_barcode,
            server_verification=False,
            barcode_pull=False,
        )
    except UserAccount.DoesNotExist:
        user_account = UserAccount.objects.create(
            user=user,
            # Default account type
            account_type="User",
        )

    if user_account.account_type.lower() == "staff":
        result = {
            "status": 'Error',
            "message": 'Staff accounts cannot generate barcodes.',
            "barcode_type": None,
            "barcode": None,
        }

    elif user_account.account_type.lower() == "user":

        # Generate a new barcode
        identification_barcode = generate_unique_identification_barcode()
        user_settings.barcode = identification_barcode
        user_settings.save()

        result = {
            "status": 'Success',
            "message": 'Temporary identification barcode generated successfully.',
            "barcode_type": 'Identification',
            "barcode": identification_barcode.barcode,
        }

    elif user_account.account_type.lower() == "school":

        if user_settings.timestamp_verification:
            ts = datetime.now(timezone.get_current_timezone()).strftime("%Y%m%d%H%M%S")
        else:
            start = datetime.now() - timedelta(days=365)
            ts_rand = random.randint(
                    0, int((datetime.now() - start).total_seconds())
                )
            ts = (start + timedelta(seconds=ts_rand)).strftime("%Y%m%d%H%M%S")
        
        if not hasattr(user_settings, 'barcode') or user_settings.barcode is None:
            user_settings.barcode_pull = True
            user_settings.save()

            dynamic_barcode = get_dynamic_barcode()

            if dynamic_barcode is None:
                result = {
                    "status": 'Error',
                    "message": 'No dynamic barcode available.',
                    "barcode_type": None,
                    "barcode": None,
                }
            else:
                result =  {
                    "status": 'Success',
                    "message": f"Dynamic: Ending with {dynamic_barcode.barcode[-4:]}",
                    "barcode_type": 'Dynamic Barcode',
                    "barcode": f"{ts}{dynamic_barcode.barcode}",
                }

        else:
            dynamic_barcode = user_settings.barcode

            if SELENIUM_ENABLED and user_settings.server_verification:
                server_result = auto_send_code(dynamic_barcode.barcode)

                if server_result["status"] == "success":
                    result = {
                        "status": 'Success',
                        "message": f"Dynamic: Ending with {dynamic_barcode.barcode[-4:]}",
                        "barcode_type": 'Dynamic Barcode',
                        "barcode": f"{ts}{dynamic_barcode.barcode}",
                    }
                


            else:
                server_result = auto_send_code(dynamic_barcode.barcode)


        return result