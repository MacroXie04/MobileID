from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_token(request):
    """
    Lightweight endpoint to issue a CSRF cookie for SPA clients.
    """
    token = get_token(request)
    return Response({"csrfToken": token})
