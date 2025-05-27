import json

from django.contrib.auth import login
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect
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
    AttestationConveyancePreference,
)

from webauthn_app.models import PasskeyCredential

RP_ID = "catcard.online"
ORIGIN = "https://catcard.online"


@require_GET
def register_options(request):
    user = request.user
    exclude = [
        {"id": c.credential_id, "type": "public-key"}
        for c in PasskeyCredential.objects.filter(user=user)
    ]

    opts = generate_registration_options(
        rp_id=RP_ID,
        rp_name="CatCard App",
        user_id=str(user.id).encode(),
        user_name=user.email,
        user_display_name=user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
            require_resident_key=True,
        ),
        attestation=AttestationConveyancePreference.NONE,
        exclude_credentials=exclude,
        timeout=60_000,
    )

    request.session["reg_opts"] = options_to_json(opts)
    return JsonResponse(json.loads(request.session["reg_opts"]))


@require_POST
def register_complete(request):
    try:
        reg_cred = parse_registration_credential_json(json.loads(request.body))
        expected = json.loads(request.session.pop("reg_opts"))

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
    except Exception:
        return redirect("webauthn_app:illegal_request")


# ---------- 登录（无用户名，自发现凭证） ---------- #
@require_GET
def auth_options(request):
    opts = generate_authentication_options(
        rp_id=RP_ID,
        user_verification=UserVerificationRequirement.REQUIRED,
        # 不提供 allow_credentials → 浏览器根据 resident key 自动匹配
        timeout=60_000,
    )
    request.session["auth_opts"] = options_to_json(opts)
    return JsonResponse(json.loads(request.session["auth_opts"]))


@require_POST
def auth_complete(request):
    try:
        auth_cred = parse_authentication_credential_json(json.loads(request.body))
        expected = json.loads(request.session.pop("auth_opts"))

        cred = PasskeyCredential.objects.get(
            credential_id=auth_cred.raw_id
        )

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
    except PasskeyCredential.DoesNotExist:
        return HttpResponseBadRequest("unknown credential")
    except Exception:
        return redirect("webauthn_app:illegal_request")
