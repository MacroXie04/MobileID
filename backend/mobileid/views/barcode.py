from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from mobileid.forms.BarcodeForm import BarcodeForm
from mobileid.models import (
    Barcode,
    UserBarcodeSettings,
    Transfer,
)

from barcode.settings import SELENIUM_ENABLED

@login_required
def create_barcode(request):
    if request.method == 'POST':
        form = BarcodeForm(request.POST)

        if form.is_valid():
            source_type = form.cleaned_data['source_type']
            input_value = form.cleaned_data['input_value']

            # init a barcode object
            barcode = Barcode(user=request.user, total_usage=0, last_used=timezone.now())
            session = None

            if source_type == 'barcode':
                # creat barcode
                if not input_value.isdigit():
                    form.add_error('input_value', "Barcode only accepts digits.")
                    return render(request, 'index/create_barcode.html', {'form': form})

                if not len(input_value) == 16:
                    form.add_error('input_value', "Barcode is not valid.")
                    return render(request, 'index/create_barcode.html', {'form': form})

                if Barcode.objects.filter(barcode=input_value, user=request.user).exists():
                    form.add_error('input_value', "Barcode already exists.")
                    return render(request, 'index/create_barcode.html', {'form': form})

                barcode.barcode = input_value
                barcode.session = None
                barcode.barcode_type = 'Static'
                barcode.save()

                # link barcode to the user
                user_barcode_settings = UserBarcodeSettings.objects.get(user=request.user)
                user_barcode_settings.barcode = barcode
                user_barcode_settings.save()
                return redirect('index')

            if source_type == 'session':
                # using the session data
                session = input_value

            if source_type == 'transfer_code':
                # using the transfer code
                if len(input_value) != 6:
                    form.add_error('input_value', "TransferCode is not valid.")
                    return render(request, 'index/create_barcode.html', {'form': form})

                try:
                    transfer_obj = Transfer.objects.get(unique_code=input_value)
                    session = transfer_obj.cookie
                    transfer_obj.delete()
                except Transfer.DoesNotExist:
                    form.add_error('input_value', "Transfer not found.")
                    return render(request, 'index/create_barcode.html', {'form': form})

            if not session:
                form.add_error('source_type', "Session is missing or invalid.")
                return render(request, 'index/create_barcode.html', {'form': form})

            # use the session to get the barcode
            server_result = uc_merced_mobile_id(session)
            if server_result['barcode'] is None:
                form.add_error('input_value', "Session Data Error.")
                return render(request, 'index/create_barcode.html', {'form': form})

            barcode_text = server_result['barcode']
            # check if the barcode already exists
            existing_barcode = Barcode.objects.filter(barcode=barcode_text).first()
            if existing_barcode:
                existing_barcode.session = session
                existing_barcode.last_used = timezone.now()
                barcode.barcode_type = 'Dynamic'
                existing_barcode.save()
                barcode = existing_barcode
            else:
                barcode.barcode = barcode_text
                barcode.session = session
                barcode.barcode_type = 'Dynamic'
                barcode.save()

            # link barcode to the user
            user_barcode_settings = UserBarcodeSettings.objects.get(user=request.user)
            user_barcode_settings.barcode = barcode
            user_barcode_settings.save()

            return redirect('index')

        # add error if the form is not valid
        form.add_error('source_type', "Please select a valid source type.")

    else:
        form = BarcodeForm()

    return render(request, 'index/create_barcode.html', {'form': form})


@login_required
def manage_barcode(request):
    # check if the user has a barcode
    if not Barcode.objects.filter(user=request.user).exists():
        return redirect('create_barcode')

    if request.method == 'POST':
        form = ManageBarcodeForm(request.POST, user=request.user)
        if form.is_valid():
            barcode = form.cleaned_data['barcode']
            # make sure is the barcode belongs to the user
            if barcode.user == request.user:
                barcode.delete()
            return redirect('manage_barcode')
    else:
        form = ManageBarcodeForm(user=request.user)

    return render(request, 'index/manage_barcode.html', {'form': form})
