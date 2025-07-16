# services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from mobileid.models import Barcode, UserAccount, UserBarcodeSettings
import uuid


class BarcodeService:

    @staticmethod
    @transaction.atomic
    def process_form(user, form_data):

        # add barcode
        barcode_type = form_data.get('barcode_type')
        barcode_value = form_data.get('barcode')

        # user settings
        barcode_choice_id = form_data.get('barcode_choice')
        server_verification = form_data.get('server_verification')
        timestamp_verification = form_data.get('timestamp_verification')
        barcode_pull = form_data.get('barcode_pull')


        # init form error
        errors = {}

        # process user account type
        user_account_type = user.UserAccount.account_type





        pass



    def update_user_settings_user(self, user, settings):
        pass

    def update_user_settings_school(self, user, settings):
        pass


    @staticmethod
    @transaction.atomic
    def create_or_update_barcode(user, form_data):



        # init form error
        errors = {}

        # process user account type
        user_account_type = user.UserAccount.account_type
