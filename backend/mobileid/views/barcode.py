from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse

from mobileid.services.barcode import generate_barcode


@login_required(login_url="/login")
@transaction.atomic
def generate_barcode_view(request):
    result = generate_barcode(request.user)
    return JsonResponse(result)
