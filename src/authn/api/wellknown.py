from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["GET"])
def webauthn_well_known(request):
    """
    WebAuthn .well-known/webauthn endpoint

    This endpoint is required by the WebAuthn specification to be accessible
    at /.well-known/webauthn on the RP ID domain.

    Returns basic WebAuthn configuration information.
    """
    return JsonResponse(
        {
            "supported_algorithms": [-7, -257],  # ES256, RS256
            "supported_attestation_types": ["none"],
            "supported_extensions": [],
            "supported_user_verification_methods": ["required"],
        }
    )
