from __future__ import annotations

import json
from typing import List, Optional
from urllib.parse import urlparse

from authn.models import PasskeyCredential
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    RegistrationCredential,
    AuthenticationCredential,
    AuthenticatorSelectionCriteria,
)


def _rp_id() -> str:
    # Require RP ID or derive strictly from BACKEND_ORIGIN (no localhost fallback)
    rp = getattr(settings, "WEBAUTHN_RP_ID", None)
    if rp:
        return rp
    backend_origin = getattr(settings, "BACKEND_ORIGIN", None)
    if not backend_origin:
        raise ImproperlyConfigured(
            "WEBAUTHN_RP_ID or BACKEND_ORIGIN must be set in environment"
        )
    parsed = urlparse(backend_origin)
    host = parsed.hostname
    if not host:
        raise ImproperlyConfigured(
            "BACKEND_ORIGIN must include a valid hostname (e.g., https://example.com)"
        )
    return host


def _origins() -> List[str]:
    allowed: List[str] = []
    backend = getattr(settings, "BACKEND_ORIGIN", None)
    if backend:
        allowed.append(backend)
    frontends = getattr(settings, "FRONTEND_ORIGINS", []) or []
    allowed.extend(frontends)

    # Normalize (strip trailing slash). Do not inject any localhost variants.
    normalized: List[str] = []
    for origin in allowed:
        if not origin:
            continue
        normalized.append(origin.rstrip("/"))

    if not normalized:
        raise ImproperlyConfigured(
            "BACKEND_ORIGIN or FRONTEND_ORIGINS must be set in environment"
        )

    # De-dup and sort for stable output
    return sorted(set(normalized))


def _pydantic_load(model_cls, data):
    """
    Load a pydantic model from a dict across v1/v2:
    - v2: model_validate
    - v1: parse_obj
    - fallback: constructor
    """
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    if hasattr(model_cls, "parse_obj"):
        return model_cls.parse_obj(data)
    try:
        return model_cls(**data)
    except Exception:
        return data


def build_registration_options(user: User, exclude_existing: bool = True) -> dict:
    exclude: List[PublicKeyCredentialDescriptor] = []
    if exclude_existing:
        existing = PasskeyCredential.objects.filter(user=user).first()
        if existing:
            exclude.append(
                PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(existing.credential_id), type="public-key"
                )
            )

    options = generate_registration_options(
        rp_id=_rp_id(),
        rp_name="MobileID",
        user_id=str(user.pk).encode("utf-8"),
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
    # Convert challenge from base64url string (stored in session) to bytes for verification
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
        f"Registration verification - expected challenge bytes length: {len(expected_bytes) if expected_bytes else 'None'}"
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


def build_authentication_options(user: Optional[User] = None) -> dict:
    allow_credentials: Optional[List[PublicKeyCredentialDescriptor]] = None
    if user is not None:
        existing = PasskeyCredential.objects.filter(user=user).first()
        if existing:
            allow_credentials = [
                PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(existing.credential_id), type="public-key"
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

    # Convert challenge from base64url string (stored in session) to bytes for verification
    # The webauthn library expects the challenge as bytes
    expected_bytes = expected_challenge
    if isinstance(expected_challenge, str):
        try:
            # Decode from base64url to bytes
            expected_bytes = base64url_to_bytes(expected_challenge)
        except Exception as e:
            print(f"Auth challenge decode error: {e}, challenge: {expected_challenge}")
            # If it's not valid base64url, treat as raw string and encode
            expected_bytes = expected_challenge.encode("utf-8")

    print(
        f"Authentication verification - expected challenge bytes length: {len(expected_bytes) if expected_bytes else 'None'}"
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
