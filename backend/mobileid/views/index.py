from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect

from mobileid.services.barcode import generate_barcode


@login_required
def index(request):
    # Redirect call back function
    return redirect("mobileid:web_login")


@login_required
def generate_barcode_view(request):
    result = generate_barcode(request.user)
    return JsonResponse(result)
