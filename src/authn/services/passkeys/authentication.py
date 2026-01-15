import json
from typing import List, Optional

from django.contrib.auth.models import User
from webauthn import generate_authentication_options, verify_authentication_response
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticationCredential,
    PublicKeyCredentialDescriptor,
)

from authn.models import PasskeyCredential

from .config import _origins, _rp_id
from .pydantic_helpers import _pydantic_load


def build_authentication_options(user: Optional[User] = None) -> dict:
    allow_credentials: Optional[List[PublicKeyCredentialDescriptor]] = None
    if user is not None:
        existing = PasskeyCredential.objects.filter(user=user).first()
        if existing:
            allow_credentials = [
                PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(existing.credential_id),
                    type="public-key",
                )
            ]

    options = generate_authentication_options(
        rp_id=_rp_id(),
        timeout=60000,
        user_verification="required",
        allow_credentials=allow_credentials,
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

    # Ensure challenge is properly formatted - use raw challenge if available
    if raw_challenge is not None:
        if isinstance(raw_challenge, bytes):
            result["challenge"] = bytes_to_base64url(raw_challenge)
        elif isinstance(raw_challenge, str):
            # Already a string - ensure it's valid base64url
            result["challenge"] = raw_challenge
    elif "challenge" in result and isinstance(result["challenge"], (bytes, bytearray)):
        result["challenge"] = bytes_to_base64url(result["challenge"])

    # Ensure allowCredentials is properly formatted if present
    if "allowCredentials" in result and isinstance(result["allowCredentials"], list):
        for cred in result["allowCredentials"]:
            if "id" in cred and isinstance(cred["id"], (bytes, bytearray)):
                cred["id"] = bytes_to_base64url(cred["id"])

    return result


def verify_authentication(credential: dict, expected_challenge) -> User:
    # Find user by credential id from response
    raw_id_b64u: str = credential.get("rawId") or credential.get("id")
    if not raw_id_b64u:
        raise ValueError("Missing credential id")

    stored = (
        PasskeyCredential.objects.filter(credential_id=raw_id_b64u)
        .select_related("user")
        .first()
    )
    if not stored:
        raise ValueError("Unknown credential")

    # Convert challenge from base64url string (stored in session) to bytes for
    # verification
    # The webauthn library expects the challenge as bytes
    expected_bytes = expected_challenge
    if isinstance(expected_challenge, str):
        try:
            # Decode from base64url to bytes
            expected_bytes = base64url_to_bytes(expected_challenge)
        except Exception as e:
            print(
                f"Auth challenge decode error: {e}, challenge: " f"{expected_challenge}"
            )
            # If it's not valid base64url, treat as raw string and encode
            expected_bytes = expected_challenge.encode("utf-8")

    print(
        f"Authentication verification - expected challenge bytes length: "
        f"{len(expected_bytes) if expected_bytes else 'None'}"
    )

    result = verify_authentication_response(
        credential=_pydantic_load(AuthenticationCredential, credential),
        expected_challenge=expected_bytes,
        expected_rp_id=_rp_id(),
        expected_origin=_origins(),
        credential_public_key=base64url_to_bytes(stored.public_key),
        credential_current_sign_count=stored.sign_count,
        require_user_verification=True,
    )

    # Update sign counter
    stored.sign_count = result.new_sign_count
    stored.save(update_fields=["sign_count", "updated_at"])

    return stored.user
