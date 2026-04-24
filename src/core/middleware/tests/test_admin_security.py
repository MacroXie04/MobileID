"""
Tests for the admin security middleware stack.

Covers:
- `_get_client_ip` — proxy header parsing and REMOTE_ADDR fallback.
- `AdminIPWhitelistMiddleware` — whitelist enforcement on the admin path only.
- `AdminAvailabilityMiddleware` — 503 short-circuit in DynamoDB-only mode.
- `AdminSessionExpiryMiddleware` — admin-scoped session expiry.
- `AdminLoginThrottleMiddleware` — rate parsing and per-IP throttling.

Middlewares read settings in ``__init__``, so each test constructs a fresh
middleware instance *inside* the ``override_settings`` context.
"""

from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from core.middleware.admin_security import (
    AdminAvailabilityMiddleware,
    AdminIPWhitelistMiddleware,
    AdminLoginThrottleMiddleware,
    AdminSessionExpiryMiddleware,
    _get_client_ip,
)


def _ok_response(_request):
    return HttpResponse("ok")


class GetClientIPTest(SimpleTestCase):
    def test_uses_x_forwarded_for_first_entry(self):
        request = RequestFactory().get(
            "/", HTTP_X_FORWARDED_FOR="203.0.113.5, 10.0.0.1"
        )
        self.assertEqual(_get_client_ip(request), "203.0.113.5")

    def test_strips_whitespace_from_forwarded_entry(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="   198.51.100.1  ")
        self.assertEqual(_get_client_ip(request), "198.51.100.1")

    def test_falls_back_to_remote_addr(self):
        request = RequestFactory().get("/", REMOTE_ADDR="127.0.0.1")
        self.assertEqual(_get_client_ip(request), "127.0.0.1")

    def test_returns_empty_string_when_nothing_available(self):
        request = RequestFactory().get("/")
        # Django's RequestFactory sets REMOTE_ADDR to 127.0.0.1 by default;
        # clear it explicitly to exercise the empty fallback.
        request.META.pop("REMOTE_ADDR", None)
        self.assertEqual(_get_client_ip(request), "")


@override_settings(ADMIN_URL_PATH="admin", ADMIN_ALLOWED_IPS=["10.0.0.5"])
class AdminIPWhitelistMiddlewareTest(SimpleTestCase):
    def _middleware(self):
        return AdminIPWhitelistMiddleware(_ok_response)

    def test_allows_non_admin_paths_regardless_of_ip(self):
        mw = self._middleware()
        response = mw(RequestFactory().get("/health/", REMOTE_ADDR="1.2.3.4"))
        self.assertEqual(response.status_code, 200)

    def test_blocks_admin_path_from_non_whitelisted_ip(self):
        mw = self._middleware()
        response = mw(RequestFactory().get("/admin/", REMOTE_ADDR="1.2.3.4"))
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"not authorized", response.content)

    def test_allows_admin_path_from_whitelisted_ip(self):
        mw = self._middleware()
        response = mw(RequestFactory().get("/admin/", REMOTE_ADDR="10.0.0.5"))
        self.assertEqual(response.status_code, 200)

    def test_uses_forwarded_header_when_present(self):
        mw = self._middleware()
        response = mw(
            RequestFactory().get(
                "/admin/",
                REMOTE_ADDR="1.2.3.4",
                HTTP_X_FORWARDED_FOR="10.0.0.5, 1.2.3.4",
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_blocks_nested_admin_paths(self):
        mw = self._middleware()
        response = mw(RequestFactory().get("/admin/login/", REMOTE_ADDR="1.2.3.4"))
        self.assertEqual(response.status_code, 403)


@override_settings(ADMIN_URL_PATH="admin", ADMIN_ALLOWED_IPS=[])
class AdminIPWhitelistMiddlewareEmptyListTest(SimpleTestCase):
    def test_empty_whitelist_allows_all_ips(self):
        """With no IPs configured, the middleware permits everything (dev mode)."""
        mw = AdminIPWhitelistMiddleware(_ok_response)
        response = mw(RequestFactory().get("/admin/", REMOTE_ADDR="1.2.3.4"))
        self.assertEqual(response.status_code, 200)


@override_settings(ADMIN_URL_PATH="admin")
class AdminAvailabilityMiddlewareTest(SimpleTestCase):
    @override_settings(PERSISTENCE_MODE="dynamodb")
    def test_returns_503_for_admin_in_dynamodb_mode(self):
        mw = AdminAvailabilityMiddleware(_ok_response)
        response = mw(RequestFactory().get("/admin/"))
        self.assertEqual(response.status_code, 503)
        self.assertIn("no-store", response["Cache-Control"])

    @override_settings(PERSISTENCE_MODE="dynamodb")
    def test_passes_through_non_admin_paths_in_dynamodb_mode(self):
        mw = AdminAvailabilityMiddleware(_ok_response)
        response = mw(RequestFactory().get("/health/"))
        self.assertEqual(response.status_code, 200)

    @override_settings(PERSISTENCE_MODE="relational")
    def test_passes_through_admin_in_relational_mode(self):
        mw = AdminAvailabilityMiddleware(_ok_response)
        response = mw(RequestFactory().get("/admin/"))
        self.assertEqual(response.status_code, 200)

    @override_settings(PERSISTENCE_MODE="hybrid")
    def test_passes_through_admin_in_hybrid_mode(self):
        mw = AdminAvailabilityMiddleware(_ok_response)
        response = mw(RequestFactory().get("/admin/"))
        self.assertEqual(response.status_code, 200)


@override_settings(ADMIN_URL_PATH="admin", ADMIN_SESSION_COOKIE_AGE=1800)
class AdminSessionExpiryMiddlewareTest(SimpleTestCase):
    class _FakeSession:
        def __init__(self):
            self.expiry = None

        def set_expiry(self, value):
            self.expiry = value

    def test_sets_shorter_expiry_on_admin_paths(self):
        request = RequestFactory().get("/admin/some-view/")
        request.session = self._FakeSession()
        mw = AdminSessionExpiryMiddleware(_ok_response)
        mw(request)
        self.assertEqual(request.session.expiry, 1800)

    def test_ignores_non_admin_paths(self):
        request = RequestFactory().get("/health/")
        request.session = self._FakeSession()
        mw = AdminSessionExpiryMiddleware(_ok_response)
        mw(request)
        self.assertIsNone(request.session.expiry)

    def test_tolerates_request_without_session(self):
        """The middleware must not blow up if SessionMiddleware hasn't run yet."""
        request = RequestFactory().get("/admin/")
        mw = AdminSessionExpiryMiddleware(_ok_response)
        response = mw(request)
        self.assertEqual(response.status_code, 200)


class AdminLoginThrottleParseRateTest(SimpleTestCase):
    """_parse_rate handles "5/15min" specially and other standard suffixes."""

    def setUp(self):
        self.mw = AdminLoginThrottleMiddleware(_ok_response)

    def test_parses_fifteen_minute_special_case(self):
        self.assertEqual(self.mw._parse_rate("5/15min"), (5, 900))

    def test_parses_minute_suffix(self):
        self.assertEqual(self.mw._parse_rate("10/1min"), (10, 60))
        self.assertEqual(self.mw._parse_rate("10/5min"), (10, 300))

    def test_parses_hour_suffix(self):
        self.assertEqual(self.mw._parse_rate("100/1hour"), (100, 3600))
        self.assertEqual(self.mw._parse_rate("50/2hour"), (50, 7200))

    def test_parses_day_suffix(self):
        self.assertEqual(self.mw._parse_rate("1000/1day"), (1000, 86400))

    def test_parses_raw_seconds_when_no_suffix(self):
        self.assertEqual(self.mw._parse_rate("5/30"), (5, 30))

    def test_returns_none_tuple_for_empty_string(self):
        self.assertEqual(self.mw._parse_rate(""), (None, None))

    def test_returns_none_tuple_for_none(self):
        self.assertEqual(self.mw._parse_rate(None), (None, None))

    def test_returns_none_tuple_for_malformed_rate(self):
        self.assertEqual(self.mw._parse_rate("not-a-rate"), (None, None))
        self.assertEqual(self.mw._parse_rate("abc/min"), (None, None))


@override_settings(
    ADMIN_URL_PATH="admin",
    REST_FRAMEWORK={"DEFAULT_THROTTLE_RATES": {"admin_login": "2/15min"}},
)
class AdminLoginThrottleMiddlewareTest(TestCase):
    """Cache-backed behavior, so use TestCase (not SimpleTestCase) for isolation."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_allows_non_post_admin_login(self):
        mw = AdminLoginThrottleMiddleware(_ok_response)
        response = mw(RequestFactory().get("/admin/login/", REMOTE_ADDR="1.2.3.4"))
        self.assertEqual(response.status_code, 200)

    def test_allows_post_to_non_login_path(self):
        mw = AdminLoginThrottleMiddleware(_ok_response)
        response = mw(RequestFactory().post("/admin/", REMOTE_ADDR="1.2.3.4"))
        self.assertEqual(response.status_code, 200)

    def test_allows_under_threshold(self):
        mw = AdminLoginThrottleMiddleware(_ok_response)
        for _ in range(2):
            response = mw(RequestFactory().post("/admin/login/", REMOTE_ADDR="1.2.3.4"))
            self.assertEqual(response.status_code, 200)

    def test_throttles_when_threshold_exceeded(self):
        mw = AdminLoginThrottleMiddleware(_ok_response)
        for _ in range(2):
            mw(RequestFactory().post("/admin/login/", REMOTE_ADDR="1.2.3.4"))
        response = mw(RequestFactory().post("/admin/login/", REMOTE_ADDR="1.2.3.4"))
        self.assertEqual(response.status_code, 429)

    def test_throttle_is_per_ip(self):
        mw = AdminLoginThrottleMiddleware(_ok_response)
        # Exhaust first IP
        for _ in range(2):
            mw(RequestFactory().post("/admin/login/", REMOTE_ADDR="1.2.3.4"))
        # A different IP should still be allowed
        response = mw(RequestFactory().post("/admin/login/", REMOTE_ADDR="5.6.7.8"))
        self.assertEqual(response.status_code, 200)

    def test_missing_client_ip_is_not_throttled(self):
        """Without an IP we can't key the counter, so the request passes."""
        mw = AdminLoginThrottleMiddleware(_ok_response)
        request = RequestFactory().post("/admin/login/")
        request.META.pop("REMOTE_ADDR", None)
        response = mw(request)
        self.assertEqual(response.status_code, 200)
