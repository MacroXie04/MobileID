import json
from typing import List

from django.contrib.auth.models import User
from webauthn import generate_registration_options, verify_registration_response
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    RegistrationCredential,
)

from authn.models import PasskeyCredential

from .config import _origins, _rp_id
from .pydantic_helpers import _pydantic_load


def build_registration_options(user: User, exclude_existing: bool = True) -> dict:
    exclude: List[PublicKeyCredentialDescriptor] = []
    if exclude_existing:
        existing = PasskeyCredential.objects.filter(user=user).first()
        if existing:
            exclude.append(
                PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(existing.credential_id),
                    type="public-key",
                )
            )

    options = generate_registration_options(
        rp_id=_rp_id(),
        rp_name="MobileID",
        # The library encodes the user_id internally; pass a string to avoid
        # calling .encode on an already-bytes value.
        user_id=str(user.pk),
        user_name=user.username,
        user_display_name=getattr(
            getattr(user, "userprofile", None), "name", user.username
        ),
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key="preferred",
            user_verification="required",
        ),
        exclude_credentials=exclude,
        attestation="none",
        supported_pub_key_algs=[-7, -257],  # ES256, RS256
    )

    # Store the raw challenge BEFORE serialization for later comparison
    raw_challenge = getattr(options, "challenge", None)

    # Serialize to plain JSON dict with WebAuthn camelCase keys when supported
    result = None
    if hasattr(options, "model_dump_json"):
        # pydantic v2
        result = json.loads(options.model_dump_json(by_alias=True))
    elif hasattr(options, "json"):
        # pydantic v1
        try:
            result = json.loads(options.json(by_alias=True))
        except TypeError:
            result = json.loads(options.json())
    elif hasattr(options, "model_dump"):
        try:
            result = options.model_dump(by_alias=True)
        except TypeError:
            result = options.model_dump()
    else:
        # Fallback: best-effort
        result = json.loads(
            json.dumps(options, default=lambda o: getattr(o, "__dict__", str(o)))
        )

    # Ensure pubKeyCredParams is present (required by WebAuthn spec)
    if "pubKeyCredParams" not in result:
        result["pubKeyCredParams"] = [
            {"type": "public-key", "alg": -7},  # ES256
            {"type": "public-key", "alg": -257},  # RS256
        ]

    # Ensure challenge is properly formatted - use raw challenge if available
    if raw_challenge is not None:
        if isinstance(raw_challenge, bytes):
            result["challenge"] = bytes_to_base64url(raw_challenge)
        elif isinstance(raw_challenge, str):
            # Already a string - ensure it's valid base64url
            result["challenge"] = raw_challenge
    elif "challenge" in result and isinstance(result["challenge"], (bytes, bytearray)):
        result["challenge"] = bytes_to_base64url(result["challenge"])

    # Ensure other required fields have proper structure
    if "user" in result and isinstance(result["user"], dict):
        # Ensure user.id is base64url encoded string
        if "id" in result["user"] and isinstance(
            result["user"]["id"], (bytes, bytearray)
        ):
            result["user"]["id"] = bytes_to_base64url(result["user"]["id"])
        # Ensure required displayName is present
        if not result["user"].get("displayName"):
            # Fall back to name if displayName missing
            result["user"]["displayName"] = result["user"].get("name") or getattr(
                getattr(user, "userprofile", None), "name", user.username
            )

    return result


def verify_and_create_passkey(
    user: User, credential: dict, expected_challenge
) -> PasskeyCredential:
    # Convert challenge from base64url string (stored in session) to bytes for
    # verification
    # The webauthn library expects the challenge as bytes
    expected_bytes = expected_challenge
    if isinstance(expected_challenge, str):
        try:
            # Decode from base64url to bytes
            expected_bytes = base64url_to_bytes(expected_challenge)
        except Exception as e:
            print(f"Challenge decode error: {e}, challenge: {expected_challenge}")
            # If it's not valid base64url, treat as raw string and encode
            expected_bytes = expected_challenge.encode("utf-8")

    print(
        f"Registration verification - expected challenge bytes length: "
        f"{len(expected_bytes) if expected_bytes else 'None'}"
    )

    verification = verify_registration_response(
        credential=_pydantic_load(RegistrationCredential, credential),
        expected_challenge=expected_bytes,
        expected_rp_id=_rp_id(),
        expected_origin=_origins(),
        require_user_verification=True,
    )

    cred_id_b64u = bytes_to_base64url(verification.credential_id)
    public_key_cose_b64u = bytes_to_base64url(verification.credential_public_key)
    sign_count = verification.sign_count

    # Enforce single passkey per user
    PasskeyCredential.objects.filter(user=user).delete()

    return PasskeyCredential.objects.create(
        user=user,
        credential_id=cred_id_b64u,
        public_key=public_key_cose_b64u,
        sign_count=sign_count,
        attestation_format=(getattr(verification, "fmt", None) or ""),
    )
