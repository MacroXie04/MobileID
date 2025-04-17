import json
import base64
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from webauthn import (
    generate_registration_options,
    generate_authentication_options,
    verify_registration_response,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes,
)
from webauthn.helpers import (
    parse_registration_credential_json,
    parse_authentication_credential_json,
)
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .models import PasskeyCredential

RP_ID = "catcard.online"
ORIGIN = "https://catcard.online"


@login_required
def register_options(request):
    user = request.user

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name="CatCard App",
        user_id=str(request.user.id).encode(),
        user_name=request.user.username,
        user_display_name=request.user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
            require_resident_key=True,  # keeps Safari ≤ 16 happy
        ),
        timeout=60_000,
    )

    request.session["reg_options"] = options_to_json(options)
    return JsonResponse(json.loads(request.session["reg_options"]))


@require_POST
@login_required
def register_complete(request):
    try:
        data = json.loads(request.body)

        reg_cred = parse_registration_credential_json(data)  # :contentReference[oaicite:0]{index=0}
        expected = json.loads(request.session.pop("reg_options"))

        verified = verify_registration_response(
            credential=reg_cred,
            expected_challenge=base64url_to_bytes(expected["challenge"]),
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            require_user_verification=True,
        )

        PasskeyCredential.objects.create(
            user=request.user,
            credential_id=verified.credential_id,
            public_key=verified.credential_public_key,
            sign_count=verified.sign_count,
        )
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@require_GET
def auth_options(request):
    options = generate_authentication_options(
        rp_id=RP_ID,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    request.session["auth_options"] = options_to_json(options)
    return JsonResponse(json.loads(request.session["auth_options"]))




@require_POST
def auth_complete(request):
    try:
        data = json.loads(request.body)

        # Decode the credential ID so it matches the BinaryField
        cred_id = base64url_to_bytes(data["id"])  # :contentReference[oaicite:2]{index=2}
        cred = PasskeyCredential.objects.get(credential_id=cred_id)
        expected = json.loads(request.session.pop("auth_options"))

        auth_cred = parse_authentication_credential_json(data)  # :contentReference[oaicite:3]{index=3}
        verified = verify_authentication_response(
            credential=auth_cred,
            expected_challenge=base64url_to_bytes(expected["challenge"]),
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=cred.public_key,
            credential_current_sign_count=cred.sign_count,
            require_user_verification=True,
        )

        cred.sign_count = verified.new_sign_count
        cred.save()
        login(request, cred.user)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return HttpResponseBadRequest(str(e))
