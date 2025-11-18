from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """
    Minimal CSP middleware.

    Adds a configurable Content-Security-Policy header unless the view already
    set one explicitly.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.policy = getattr(settings, "CSP_DEFAULT_POLICY", "")

    def __call__(self, request):
        response = self.get_response(request)
        if self.policy and not response.has_header("Content-Security-Policy"):
            response["Content-Security-Policy"] = self.policy
        return response
