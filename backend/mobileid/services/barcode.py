import random
import time
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from mobileid.models import UserBarcodeSettings, Barcode, UserAccount, BarcodeUsage
from mobileid.project_code.barcode import auto_send_code
from barcode.settings import SELENIUM_ENABLED


def generate_unique_identification_barcode():
    """
    Generate a unique 28-digit identification barcode.
    Uses a while loop to ensure uniqueness by checking against existing barcodes.
    """
    while True:
        code = ''.join([str(random.randint(0, 9)) for _ in range(28)])
        if not Barcode.objects.filter(barcode=code).exists():
            return code


def update_user_identification_barcode(user):
    """
    Get user identification barcode (function appears incomplete).
    """
    user_identification_barcode = Barcode.objects.filter(
        user=user, barcode_type="Identification"
    )


def get_dynamic_barcode():
    """
    Get the least used dynamic barcode based on usage statistics.
    Returns the barcode with lowest total_usage and oldest last_used timestamp.
    """
    # Select dynamic barcodes with their usage statistics in a single query
    barcode_with_usage = BarcodeUsage.objects.filter(
        barcode__barcode_type="DynamicBarcode"
    ).select_related('barcode').order_by('total_usage', 'last_used')

    if barcode_with_usage.exists():
        selected_usage = barcode_with_usage.first()
        return selected_usage.barcode
    else:
        return None
    

def update_dynamic_barcode_usage(barcode):
    """
    Update barcode usage statistics atomically.
    Uses F() expressions to avoid race conditions and reduce database queries.
    """
    barcode_usage, created = BarcodeUsage.objects.get_or_create(
        barcode=barcode,
        defaults={'total_usage': 0, 'last_used': timezone.now()}
    )
    
    # Use F() expression for atomic update to prevent race conditions
    BarcodeUsage.objects.filter(barcode=barcode).update(
        total_usage=F('total_usage') + 1,
        last_used=timezone.now()
    )


@transaction.atomic
def generate_barcode(user):
    """
    Generate barcode for user based on their account type.
    Uses database transaction to ensure data consistency.
    Optimized to reduce database queries by using select_related.
    """
    # Get user account and settings in optimized queries
    try:
        user_account = UserAccount.objects.get(user=user)
    except UserAccount.DoesNotExist:
        # Create default user account if it doesn't exist
        user_account = UserAccount.objects.create(
            user=user,
            account_type="User",
        )

    # Get or create user settings with related barcode in single query
    try:
        user_settings = UserBarcodeSettings.objects.select_related('barcode').get(user=user)
    except UserBarcodeSettings.DoesNotExist:
        # Create identification barcode and user settings
        user_identification_barcode = Barcode.objects.create(
            user=user,
            barcode_type="Identification",
            barcode=generate_unique_identification_barcode(),
        )

        user_settings = UserBarcodeSettings.objects.create(
            user=user,
            barcode=user_identification_barcode,
            server_verification=False,
            barcode_pull=False,
        )

    # Handle different account types
    account_type = user_account.account_type.lower()
    
    if account_type == "staff":
        result = {
            "status": 'Error',
            "message": 'Staff accounts cannot generate barcodes.',
            "barcode_type": None,
            "barcode": None,
        }

    elif account_type == "user":
        # Generate new identification barcode for regular users
        new_barcode_code = generate_unique_identification_barcode()

        # delete existing identification barcode
        Barcode.objects.filter(user=user, barcode_type="Identification").delete()
        identification_barcode = Barcode.objects.create(
            user=user,
            barcode_type="Identification",
            barcode=new_barcode_code,
        )
        user_settings.barcode = identification_barcode

        user_settings.save(update_fields=['barcode'])

        result = {
            "status": 'Success',
            "message": 'Temporary identification barcode generated successfully.',
            "barcode_type": 'Identification',
            "barcode": new_barcode_code,
        }

    elif account_type == "school":
        print("School account found")
        # Generate timestamp for school accounts
        if user_settings.timestamp_verification:
            ts = datetime.now(timezone.get_current_timezone()).strftime("%Y%m%d%H%M%S")
        else:
            # Generate random timestamp within the last year
            start = datetime.now() - timedelta(days=365)
            ts_rand = random.randint(
                0, int((datetime.now() - start).total_seconds())
            )
            ts = (start + timedelta(seconds=ts_rand)).strftime("%Y%m%d%H%M%S")
        
        # Handle dynamic barcode assignment
        if user_settings.barcode.barcode_type.lower() == "identification":
            print("Identification barcode found")
            Barcode.objects.filter(user=user, barcode_type="Identification").delete()

        if not user_settings.barcode.barcode_type.lower() == "dynamicbarcode":
            # User doesn't have assigned barcode, get one from pool
            user_settings.barcode_pull = True
            
            dynamic_barcode = get_dynamic_barcode()

            if dynamic_barcode is None:
                result = {
                    "status": 'Error',
                    "message": 'No dynamic barcode available.',
                    "barcode_type": None,
                    "barcode": None,
                }
            else:
                # Assign barcode to user and update usage
                user_settings.barcode = dynamic_barcode
                user_settings.save(update_fields=['barcode', 'barcode_pull'])
                update_dynamic_barcode_usage(dynamic_barcode)

                result = {
                    "status": 'Success',
                    "message": f"Dynamic: Ending with {dynamic_barcode.barcode[-4:]}",
                    "barcode_type": 'Dynamic Barcode',
                    "barcode": f"{ts}{dynamic_barcode.barcode}",
                }
        else:
            # User already has assigned barcode
            dynamic_barcode = user_settings.barcode
            update_dynamic_barcode_usage(dynamic_barcode)

            # Handle server verification if enabled
            if SELENIUM_ENABLED and user_settings.server_verification:
                server_result = auto_send_code(dynamic_barcode.barcode)

                if server_result["status"] == "success":
                    result = {
                        "status": 'Success',
                        "message": f"Dynamic: Server: {server_result['code']}",
                        "barcode_type": 'Dynamic Barcode',
                        "barcode": f"{ts}{dynamic_barcode.barcode}",
                    }
                else:
                    result = {
                        "status": 'Success',
                        "message": f"Dynamic: Ending with {dynamic_barcode.barcode[-4:]}",
                        "barcode_type": 'Dynamic Barcode',
                        "barcode": f"{ts}{dynamic_barcode.barcode}",
                    }
            else:
                result = {
                    "status": 'Success',
                    "message": f"Dynamic: Ending with {dynamic_barcode.barcode[-4:]}",
                    "barcode_type": 'Dynamic Barcode',
                    "barcode": f"{ts}{dynamic_barcode.barcode}",
                }
    else:
        # Handle unknown account types
        result = {
            "status": 'Error',
            "message": f'Unknown account type: {account_type}',
            "barcode_type": None,
            "barcode": None,
        }

    return result