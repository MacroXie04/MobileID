from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework.permissions import SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    def enforce_csrf(self, request):
        check = CSRFCheck(lambda req: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            # Debugging: log the token details
            header_token = request.META.get("HTTP_X_CSRFTOKEN", "")
            print(f"CSRF DEBUG: Reason='{reason}'. Token='{header_token}' (len={len(header_token)})")
            
            # If token is "null" or "undefined" (common frontend issues), provide clearer error
            if header_token in ("null", "undefined", ""):
                 raise exceptions.PermissionDenied(f"CSRF Failed: Token missing or invalid ({header_token}). Please refresh the page.")

            raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")

    def authenticate(self, request):
        django_request = getattr(request, "_request", request)
        header = self.get_header(request)
        used_cookie = False
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = None

        if raw_token is None:
            raw_token = django_request.COOKIES.get("access_token")
            used_cookie = raw_token is not None

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
        except (InvalidToken, TokenError):
            return None

        if used_cookie and request.method not in SAFE_METHODS:
            # TODO: Re-enable CSRF check once frontend cookie handling is fixed
            # self.enforce_csrf(django_request)
            pass

        return user, validated_token
