"""
Content Security Policy and security headers middleware.
"""

from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """
    Adds configurable security headers unless the view already set them.

    Headers managed:
    - Content-Security-Policy (or Content-Security-Policy-Report-Only)
    - Permissions-Policy
    - Cross-Origin-Opener-Policy
    - Cross-Origin-Resource-Policy
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.policy = getattr(settings, "CSP_DEFAULT_POLICY", "")
        self.csp_report_only = getattr(settings, "CSP_REPORT_ONLY", False)
        self.permissions_policy = getattr(settings, "PERMISSIONS_POLICY", "")
        self.coop = getattr(settings, "CROSS_ORIGIN_OPENER_POLICY", "")
        self.corp = getattr(settings, "CROSS_ORIGIN_RESOURCE_POLICY", "")

    def __call__(self, request):
        response = self.get_response(request)

        if self.policy:
            if self.csp_report_only:
                if not response.has_header("Content-Security-Policy-Report-Only"):
                    response["Content-Security-Policy-Report-Only"] = self.policy
            else:
                if not response.has_header("Content-Security-Policy"):
                    response["Content-Security-Policy"] = self.policy

        if self.permissions_policy and not response.has_header("Permissions-Policy"):
            response["Permissions-Policy"] = self.permissions_policy

        if self.coop and not response.has_header("Cross-Origin-Opener-Policy"):
            response["Cross-Origin-Opener-Policy"] = self.coop

        if self.corp and not response.has_header("Cross-Origin-Resource-Policy"):
            response["Cross-Origin-Resource-Policy"] = self.corp

        return response
