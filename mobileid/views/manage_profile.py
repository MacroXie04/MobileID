from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from mobileid.forms.BarcodeForm import BarcodeForm
from mobileid.forms.SetupForm import SetupForm
from mobileid.forms.ManageBarcodeForm import ManageBarcodeForm
from mobileid.forms.UserBarcodeSettingsForm import UserBarcodeSettingsForm
from mobileid.models import StudentInformation, Barcode, Transfer, UserBarcodeSettings
from mobileid.project_code.barcode import uc_merced_mobile_id


@login_required(login_url='/login/')
def setup(request):
    user_profile, created = StudentInformation.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = SetupForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            user_profile.name = data.get('name')
            user_profile.student_id = data.get('student_id')

            if 'avatar' in request.FILES:
                user_profile.avatar = request.FILES['avatar']

            user_profile.save()
            return redirect('index')
    else:
        form = SetupForm(initial={
            'name': user_profile.name,
            'student_id': user_profile.student_id,
        })

    return render(request, 'setup.html', {'form': form})


@login_required(login_url='/login/')
def settings(request):
    # get or create user barcode settings
    user_settings, created = UserBarcodeSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserBarcodeSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            # save the data to database
            form.save()
            return redirect('index')
    else:
        form = UserBarcodeSettingsForm(instance=user_settings)

    return render(request, 'settings.html', {'form': form})


@login_required(login_url='/login/')
def create_barcode(request):
    if request.method == 'POST':
        form = BarcodeForm(request.POST)

        if form.is_valid():
            source_type = form.cleaned_data['source_type']
            input_value = form.cleaned_data['input_value']

            barcode = Barcode(user=request.user, total_usage=0, last_used=timezone.now())
            session = None

            if source_type == 'barcode':
                # Check that the barcode has the correct length.
                if not 10 < len(input_value) < 20:
                    form.add_error('input_value', "Barcode is not valid.")
                    return render(request, 'create_barcode.html', {'form': form})

                # Use the barcode directly.
                barcode.barcode = input_value
                barcode.session = None
                barcode.save()

                # Link the new barcode to the user.
                user_barcode_settings = UserBarcodeSettings.objects.get(user=request.user)
                user_barcode_settings.barcode = barcode
                user_barcode_settings.save()
                return redirect('index')

            if source_type == 'session':
                # use the session directly.
                session = input_value

            if source_type == 'transfer_code':
                # Check that the transfer code has the correct length.
                if len(input_value) != 6:
                    form.add_error('input_value', "TransferCode is not valid.")
                    return render(request, 'create_barcode.html', {'form': form})
                print("transfer_code:", input_value)
                try:
                    transfer_obj = Transfer.objects.get(unique_code=input_value)
                    session = transfer_obj.cookie
                    transfer_obj.delete()
                except Transfer.DoesNotExist:
                    form.add_error('input_value', "Transfer not found.")
                    return render(request, 'create_barcode.html', {'form': form})

            if not session:
                form.add_error('source_type', "Session is missing or invalid.")
                return render(request, 'create_barcode.html', {'form': form})

            # Use the session to get the barcode from the server.
            server_result = uc_merced_mobile_id(session)
            if server_result['barcode'] is None:
                form.add_error('input_value', "Session Data Error.")
                return render(request, 'create_barcode.html', {'form': form})

            # Save barcode to the database.
            barcode.barcode = server_result['barcode']
            barcode.session = session
            barcode.save()

            # Link barcode to the user.
            user_barcode_settings = UserBarcodeSettings.objects.get(user=request.user)
            user_barcode_settings.barcode = barcode
            user_barcode_settings.save()

            return redirect('index')

        # When form validation fails, add a generic error.
        form.add_error('source_type', "Please select a valid source type.")

    else:
        form = BarcodeForm()

    return render(request, 'create_barcode.html', {'form': form})


@login_required(login_url='/login/')
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

    return render(request, 'manage_barcode.html', {'form': form})