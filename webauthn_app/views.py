import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from webauthn.helpers.structs import *
from webauthn import *
from .models import PasskeyCredential
from django.contrib.auth.models import User

RP_ID = "catcard.online"
ORIGIN = "https://catcard.online"

@login_required
def register_options(request):
    user = request.user
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name="CatCard App",
        user_id=str(user.id),
        user_name=user.username,
        user_display_name=user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key="required",
            user_verification="required",
        ),
    )
    request.session['reg_options'] = options_to_json(options)
    return JsonResponse(json.loads(request.session['reg_options']))

@require_POST
@login_required
def register_complete(request):
    try:
        import base64

        def base64url_to_bytes(val):
            val += '=' * ((4 - len(val) % 4) % 4)
            return base64.urlsafe_b64decode(val)

        def bytes_to_base64url(b):
            return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')

        data = json.loads(request.body)
        print("🟡 ID =", data['id'])
        print("🟡 RAW ID =", data['rawId'])
        print("🟡 type(id):", type(data['id']))
        print("🟡 type(rawId):", type(data['rawId']))

        # force overwrite id using rawId
        if isinstance(data['rawId'], list):
            raw_bytes = bytes(data['rawId'])
        else:
            raw_bytes = base64url_to_bytes(data['rawId'])

        data['id'] = bytes_to_base64url(raw_bytes)

        reg_cred = RegistrationCredential.parse_obj(data)
        expected = json.loads(request.session.pop('reg_options'))

        verified = verify_registration_response(
            credential=reg_cred,
            expected_challenge=expected['challenge'],
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
        import traceback
        traceback.print_exc()
        return HttpResponseBadRequest(str(e))

@require_GET
def auth_options(request):
    options = generate_authentication_options(
        rp_id=RP_ID,
        user_verification="required",
    )
    request.session['auth_options'] = options_to_json(options)
    return JsonResponse(json.loads(request.session['auth_options']))

@require_POST
def auth_complete(request):
    try:
        data = json.loads(request.body)
        credential_id = data['id']

        cred = PasskeyCredential.objects.get(credential_id=credential_id)
        user = cred.user
        expected = json.loads(request.session.pop('auth_options'))

        verified = verify_authentication_response(
            credential=AuthenticationCredential.parse_obj(data),
            expected_challenge=expected['challenge'],
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=cred.public_key,
            credential_current_sign_count=cred.sign_count,
            require_user_verification=True,
        )

        cred.sign_count = verified.new_sign_count
        cred.save()

        login(request, user)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return HttpResponseBadRequest(str(e))
