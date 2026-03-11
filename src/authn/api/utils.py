from django.conf import settings

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/authn/"


def _cookie_secure(request):
    if request is None:
        return settings.SESSION_COOKIE_SECURE
    if request.is_secure():
        return True
    return settings.SESSION_COOKIE_SECURE


def _cookie_samesite():
    return getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax") or "Lax"


def _access_max_age():
    lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
    return int(lifetime.total_seconds())


def _refresh_max_age():
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    return int(lifetime.total_seconds())


def set_auth_cookies(response, access_token, refresh_token, request=None):
    cookie_kwargs = {
        "httponly": True,
        "secure": _cookie_secure(request),
        "samesite": _cookie_samesite(),
    }

    response.set_cookie(
        ACCESS_COOKIE_NAME,
        access_token,
        max_age=_access_max_age(),
        **cookie_kwargs,
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=_refresh_max_age(),
        path=REFRESH_COOKIE_PATH,
        **cookie_kwargs,
    )
    return response


def clear_auth_cookies(response):
    # Use set_cookie with max_age=0 instead of delete_cookie so we can pass
    # samesite and secure flags that match the original cookie attributes.
    # delete_cookie() defaults to SameSite=Lax without Secure, which won't
    # clear cookies originally set with SameSite=None; Secure=True.
    common = {
        "max_age": 0,
        "httponly": True,
        "samesite": _cookie_samesite(),
        "secure": _cookie_secure(None),
    }
    response.set_cookie(ACCESS_COOKIE_NAME, "", **common)
    response.set_cookie(REFRESH_COOKIE_NAME, "", path=REFRESH_COOKIE_PATH, **common)
    return response
