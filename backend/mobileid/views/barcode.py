from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from mobileid.services.barcode import generate_barcode

# @transaction.atomic
@login_required
def generate_barcode_view(request):
    result = generate_barcode(request.user)
    return JsonResponse(result)
