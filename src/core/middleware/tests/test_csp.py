"""
Tests for ContentSecurityPolicyMiddleware.

Exercises the middleware directly with minimal request/response pairs so we can
assert header behavior for every policy setting without spinning up the full
request stack.
"""

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from core.middleware.csp import ContentSecurityPolicyMiddleware


def _run(**response_kwargs):
    """Return (middleware, request, response) triple for the given setup."""

    def get_response(request):
        response = HttpResponse("ok")
        for header, value in response_kwargs.items():
            response[header] = value
        return response

    middleware = ContentSecurityPolicyMiddleware(get_response)
    request = RequestFactory().get("/")
    return middleware, request, middleware(request)


@override_settings(
    CSP_DEFAULT_POLICY="default-src 'self'",
    CSP_REPORT_ONLY=False,
    PERMISSIONS_POLICY="camera=()",
    CROSS_ORIGIN_OPENER_POLICY="same-origin",
    CROSS_ORIGIN_RESOURCE_POLICY="same-site",
)
class CSPMiddlewareTest(TestCase):
    def test_sets_all_security_headers_when_configured(self):
        _, _, response = _run()

        self.assertEqual(response["Content-Security-Policy"], "default-src 'self'")
        self.assertEqual(response["Permissions-Policy"], "camera=()")
        self.assertEqual(response["Cross-Origin-Opener-Policy"], "same-origin")
        self.assertEqual(response["Cross-Origin-Resource-Policy"], "same-site")
        self.assertNotIn("Content-Security-Policy-Report-Only", response.headers)

    @override_settings(CSP_REPORT_ONLY=True)
    def test_uses_report_only_header_when_flag_enabled(self):
        _, _, response = _run()

        self.assertEqual(
            response["Content-Security-Policy-Report-Only"], "default-src 'self'"
        )
        self.assertNotIn("Content-Security-Policy", response.headers)

    def test_does_not_overwrite_csp_already_set_by_view(self):
        _, _, response = _run(**{"Content-Security-Policy": "default-src 'none'"})

        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")

    @override_settings(CSP_REPORT_ONLY=True)
    def test_does_not_overwrite_report_only_already_set_by_view(self):
        _, _, response = _run(
            **{"Content-Security-Policy-Report-Only": "default-src 'none'"}
        )

        self.assertEqual(
            response["Content-Security-Policy-Report-Only"], "default-src 'none'"
        )

    def test_does_not_overwrite_permissions_policy_already_set(self):
        _, _, response = _run(**{"Permissions-Policy": "camera=(self)"})

        self.assertEqual(response["Permissions-Policy"], "camera=(self)")

    def test_does_not_overwrite_coop_already_set(self):
        _, _, response = _run(**{"Cross-Origin-Opener-Policy": "unsafe-none"})

        self.assertEqual(response["Cross-Origin-Opener-Policy"], "unsafe-none")

    def test_does_not_overwrite_corp_already_set(self):
        _, _, response = _run(**{"Cross-Origin-Resource-Policy": "cross-origin"})

        self.assertEqual(response["Cross-Origin-Resource-Policy"], "cross-origin")


@override_settings(
    CSP_DEFAULT_POLICY="",
    PERMISSIONS_POLICY="",
    CROSS_ORIGIN_OPENER_POLICY="",
    CROSS_ORIGIN_RESOURCE_POLICY="",
)
class CSPMiddlewareDisabledTest(TestCase):
    def test_no_headers_added_when_all_settings_empty(self):
        _, _, response = _run()

        self.assertNotIn("Content-Security-Policy", response.headers)
        self.assertNotIn("Content-Security-Policy-Report-Only", response.headers)
        self.assertNotIn("Permissions-Policy", response.headers)
        self.assertNotIn("Cross-Origin-Opener-Policy", response.headers)
        self.assertNotIn("Cross-Origin-Resource-Policy", response.headers)


class CSPMiddlewareDefaultsTest(TestCase):
    """
    When no CSP_* settings are defined, the middleware must fall back to empty
    strings (via getattr defaults) and not raise.
    """

    def test_missing_settings_do_not_raise(self):
        with self.settings():
            # Settings intentionally unchanged — whatever the default test
            # settings provide is what we want to exercise here.
            _, _, response = _run()

        self.assertEqual(response.status_code, 200)
