"""Tests for authn.api.webauthn.views.devices.utils helpers."""

from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from authn.api.webauthn.views.devices.utils import (
    _get_current_refresh_token_jti,
    _get_current_session_iat,
    _parse_device_info,
)


def _make_request(data=None, cookies=None, auth=None):
    """Build a lightweight DRF-like request for the utils under test."""
    request = RequestFactory().post("/")
    request.data = data if data is not None else {}
    if cookies:
        request.COOKIES.update(cookies)
    request.auth = auth
    return request


class GetCurrentSessionIatTest(TestCase):
    def test_returns_iat_when_present_in_auth(self):
        request = _make_request(auth={"iat": 1700000000, "jti": "abc"})

        self.assertEqual(_get_current_session_iat(request), 1700000000)

    def test_returns_none_when_no_auth(self):
        request = _make_request(auth=None)

        self.assertIsNone(_get_current_session_iat(request))

    def test_returns_none_when_iat_missing_from_auth(self):
        request = _make_request(auth={"jti": "abc"})

        self.assertIsNone(_get_current_session_iat(request))

    def test_returns_none_when_request_has_no_auth_attribute(self):
        request = SimpleNamespace()  # no `.auth`

        self.assertIsNone(_get_current_session_iat(request))


class GetCurrentRefreshTokenJtiTest(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="jti", password="pw")

    def test_uses_body_current_jti_when_provided(self):
        request = _make_request(data={"current_jti": "from-body"})

        self.assertEqual(_get_current_refresh_token_jti(request), "from-body")

    def test_falls_back_to_refresh_cookie(self):
        refresh = RefreshToken.for_user(self.user)
        request = _make_request(cookies={"refresh_token": str(refresh)})

        jti = _get_current_refresh_token_jti(request)
        self.assertEqual(jti, refresh["jti"])

    def test_body_takes_priority_over_cookie(self):
        refresh = RefreshToken.for_user(self.user)
        request = _make_request(
            data={"current_jti": "body-wins"},
            cookies={"refresh_token": str(refresh)},
        )

        self.assertEqual(_get_current_refresh_token_jti(request), "body-wins")

    def test_returns_none_when_nothing_provided(self):
        request = _make_request()

        self.assertIsNone(_get_current_refresh_token_jti(request))

    def test_returns_none_when_body_current_jti_empty_string(self):
        refresh = RefreshToken.for_user(self.user)
        request = _make_request(
            data={"current_jti": ""},
            cookies={"refresh_token": str(refresh)},
        )

        # Empty string should not win over the cookie fallback.
        self.assertEqual(_get_current_refresh_token_jti(request), refresh["jti"])

    def test_returns_none_when_body_current_jti_not_a_string(self):
        request = _make_request(data={"current_jti": 12345})

        self.assertIsNone(_get_current_refresh_token_jti(request))

    def test_returns_none_when_cookie_is_malformed(self):
        request = _make_request(cookies={"refresh_token": "not-a-jwt"})

        self.assertIsNone(_get_current_refresh_token_jti(request))


class ParseDeviceInfoTest(TestCase):
    def test_unknown_device_when_user_agent_empty(self):
        self.assertEqual(
            _parse_device_info(""),
            {
                "device_name": "Unknown Device",
                "browser": "Unknown",
                "os": "Unknown",
                "device_type": "unknown",
            },
        )

    def test_unknown_device_when_user_agent_none(self):
        info = _parse_device_info(None)

        self.assertEqual(info["device_name"], "Unknown Device")
        self.assertEqual(info["device_type"], "unknown")

    def test_detects_iphone(self):
        ua = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
            "Mobile/15E148 Safari/604.1"
        )
        info = _parse_device_info(ua)

        self.assertEqual(info["os"], "iOS")
        self.assertEqual(info["device_type"], "mobile")
        self.assertEqual(info["browser"], "Safari")
        self.assertEqual(info["device_name"], "Safari on iOS")

    def test_detects_ipad(self):
        ua = "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) Safari/604.1"
        info = _parse_device_info(ua)

        self.assertEqual(info["os"], "iOS")
        self.assertEqual(info["device_type"], "tablet")

    def test_detects_android_mobile(self):
        ua = (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        )
        info = _parse_device_info(ua)

        self.assertEqual(info["os"], "Android")
        self.assertEqual(info["device_type"], "mobile")
        self.assertEqual(info["browser"], "Chrome")

    def test_detects_android_tablet(self):
        ua = (
            "Mozilla/5.0 (Linux; Android 13; SM-X900) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        info = _parse_device_info(ua)

        self.assertEqual(info["os"], "Android")
        self.assertEqual(info["device_type"], "tablet")

    def test_detects_macos_safari(self):
        ua = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        )
        info = _parse_device_info(ua)

        self.assertEqual(info["os"], "macOS")
        self.assertEqual(info["device_type"], "desktop")
        self.assertEqual(info["browser"], "Safari")

    def test_detects_windows_edge(self):
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        )
        info = _parse_device_info(ua)

        self.assertEqual(info["os"], "Windows")
        self.assertEqual(info["browser"], "Edge")

    def test_detects_linux_firefox(self):
        ua = "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
        info = _parse_device_info(ua)

        self.assertEqual(info["os"], "Linux")
        self.assertEqual(info["browser"], "Firefox")
        self.assertEqual(info["device_type"], "desktop")

    def test_detects_chromeos(self):
        ua = (
            "Mozilla/5.0 (X11; CrOS x86_64 15662.76.0) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        info = _parse_device_info(ua)

        self.assertEqual(info["os"], "Chrome OS")
        self.assertEqual(info["device_type"], "desktop")

    def test_detects_opera(self):
        ua = (
            "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0"
        )
        info = _parse_device_info(ua)

        self.assertEqual(info["browser"], "Opera")

    def test_detects_internet_explorer(self):
        ua = "Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko"
        info = _parse_device_info(ua)

        self.assertEqual(info["browser"], "Internet Explorer")

    def test_unknown_browser_and_os(self):
        info = _parse_device_info("SomeCustomBot/1.0")

        self.assertEqual(info["os"], "Unknown")
        self.assertEqual(info["browser"], "Unknown Browser")
        self.assertEqual(info["device_type"], "unknown")
        self.assertEqual(info["device_name"], "Unknown Browser on Unknown")
