from datetime import datetime, timedelta

import pytz
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from mobileid.forms.BarcodeForm import ManageBarcodeForm
from mobileid.models import Barcode, BarcodeUsage, UserBarcodeSettings

from mobileid.services.barcode import generate_barcode



@login_required(login_url="/login")
@transaction.atomic
def generate_barcode_view(request):
    result = generate_barcode(request.user)
    return JsonResponse(result)