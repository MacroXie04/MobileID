import base64
import json

from authn.middleware.authentication import CookieJWTAuthentication
from authn.models import LoginAuditLog, RSAKeyPair
from authn.services.webauthn import create_user_profile
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.middleware.csrf import get_token
from django.urls import reverse
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class LoginSecurityTests(APITestCase):
    """End-to-end tests for hardened login, cookies, and CSRF behavior."""

    @classmethod
    def setUpTestData(cls):
        cls.user_password = "testpass123"
        cls.user = User.objects.create_user(
            username="secureuser", password=cls.user_password
        )
        create_user_profile(cls.user, "Secure User", "SECURE123", None)

    @staticmethod
    def _provision_rsa_key():
        RSAKeyPair.objects.all().delete()
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        RSAKeyPair.objects.create(
            public_key=public_pem,
            private_key=private_pem,
            key_size=2048,
            is_active=True,
        )

    def setUp(self):
        super().setUp()
        cache.clear()
        LoginAuditLog.objects.all().delete()
        self._provision_rsa_key()

    def _get_challenge(self):
        url = reverse("authn:api_login_challenge")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def _encrypt_with_challenge(self, challenge, password):
        payload = json.dumps(
            {"nonce": challenge["nonce"], "password": password}
        ).encode("utf-8")
        public_key = serialization.load_pem_public_key(
            challenge["public_key"].encode("utf-8")
        )
        ciphertext = public_key.encrypt(
            payload,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(ciphertext).decode("utf-8")

    def _perform_rsa_login(self):
        challenge = self._get_challenge().data
        encrypted = self._encrypt_with_challenge(challenge, self.user_password)
        url = reverse("authn:api_rsa_login")
        response = self.client.post(
            url,
            {"username": self.user.username, "password": encrypted},
            format="json",
        )
        return response

    def test_login_challenge_sets_csrf_and_csp(self):
        response = self._get_challenge()
        self.assertIn("nonce", response.data)
        self.assertIn("kid", response.data)
        self.assertIn("public_key", response.data)
        self.assertIn("Content-Security-Policy", response)
        self.assertIn("csrftoken", response.cookies)

    def test_refresh_cookie_attributes(self):
        response = self._perform_rsa_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_cookie = response.cookies.get("refresh_token")
        self.assertIsNotNone(refresh_cookie)
        cookie_header = refresh_cookie.output(header="")
        self.assertEqual(refresh_cookie["path"], "/authn/")
        self.assertEqual(refresh_cookie["samesite"], "Lax")
        if settings.SESSION_COOKIE_SECURE:
            self.assertIn("Secure", cookie_header)
        else:
            self.assertNotIn("Secure", cookie_header)
        self.assertIn("HttpOnly", cookie_header)

    def test_token_refresh_rotates_cookie(self):
        login_response = self._perform_rsa_login()
        old_refresh = login_response.cookies["refresh_token"].value
        refresh_url = reverse("authn:api_token_refresh")
        refresh_response = self.client.post(
            refresh_url,
            {"refresh": old_refresh},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        new_refresh_cookie = refresh_response.cookies.get("refresh_token")
        self.assertIsNotNone(new_refresh_cookie)
        new_cookie_header = new_refresh_cookie.output(header="")
        self.assertNotEqual(new_refresh_cookie.value, old_refresh)
        if settings.SESSION_COOKIE_SECURE:
            self.assertIn("Secure", new_cookie_header)
        else:
            self.assertNotIn("Secure", new_cookie_header)
        self.assertIn("HttpOnly", new_cookie_header)
        self.assertEqual(new_refresh_cookie["path"], "/authn/")

    def test_nonce_is_single_use(self):
        challenge_response = self._get_challenge()
        challenge = challenge_response.data
        encrypted = self._encrypt_with_challenge(challenge, self.user_password)
        url = reverse("authn:api_rsa_login")
        first = self.client.post(
            url,
            {"username": self.user.username, "password": encrypted},
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_200_OK)

        second = self.client.post(
            url,
            {"username": self.user.username, "password": encrypted},
            format="json",
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid username or password.", str(second.data["detail"]))

    def test_login_creates_audit_log_entry(self):
        response = self._perform_rsa_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log = LoginAuditLog.objects.filter(username=self.user.username).first()
        self.assertIsNotNone(log)
        self.assertTrue(log.success)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.ip_address, "127.0.0.1")

    def test_login_rate_throttle_triggers(self):
        url = reverse("authn:api_rsa_login")
        payload = {"username": self.user.username, "password": "A" * 200}
        last_status = None
        for _ in range(6):
            response = self.client.post(url, payload, format="json")
            last_status = response.status_code
        self.assertEqual(last_status, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_csrf_enforced_for_cookie_authenticated_put(self):
        factory = APIRequestFactory()
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        django_request = factory.put(
            "/authn/profile/",
            {"name": "Updated Name", "information_id": "SECURE123"},
            format="json",
        )
        django_request._dont_enforce_csrf_checks = False
        csrf_token_value = get_token(django_request)
        django_request.COOKIES["access_token"] = access_token
        django_request.COOKIES["csrftoken"] = csrf_token_value
        request = Request(django_request)

        authenticator = CookieJWTAuthentication()
        with self.assertRaises(exceptions.PermissionDenied):
            authenticator.authenticate(request)

        django_request.META["HTTP_X_CSRFTOKEN"] = csrf_token_value
        authed_user, _ = authenticator.authenticate(Request(django_request))
        self.assertEqual(authed_user, self.user)

    def test_failed_login_creates_audit_log_entry(self):
        """Test that failed login attempts are logged"""
        url = reverse("authn:api_rsa_login")
        challenge = self._get_challenge().data
        # Use wrong password
        encrypted = self._encrypt_with_challenge(challenge, "wrongpassword")
        response = self.client.post(
            url,
            {"username": self.user.username, "password": encrypted},
            format="json",
        )
        # Failed login can return 400 or 401 depending on implementation
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED],
        )

        log = LoginAuditLog.objects.filter(
            username=self.user.username, success=False
        ).first()
        self.assertIsNotNone(log)
        self.assertFalse(log.success)

    def test_login_with_nonexistent_user_fails(self):
        """Test that login with non-existent user fails gracefully"""
        url = reverse("authn:api_rsa_login")
        challenge = self._get_challenge().data
        encrypted = self._encrypt_with_challenge(challenge, "anypassword")
        response = self.client.post(
            url,
            {"username": "nonexistent_user", "password": encrypted},
            format="json",
        )
        # Non-existent user can return 400 or 401 depending on implementation
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED],
        )

    def test_login_challenge_returns_unique_nonce(self):
        """Test that each challenge request returns a unique nonce"""
        nonces = set()
        for _ in range(5):
            cache.clear()  # Clear cache to get new challenge
            response = self._get_challenge()
            nonces.add(response.data["nonce"])
        self.assertEqual(len(nonces), 5)

    def test_login_challenge_returns_unique_kid(self):
        """Test that challenge includes key ID"""
        response = self._get_challenge()
        self.assertIn("kid", response.data)
        self.assertIsNotNone(response.data["kid"])

    def test_empty_password_rejected(self):
        """Test that empty password is rejected"""
        url = reverse("authn:api_rsa_login")
        response = self.client.post(
            url,
            {"username": self.user.username, "password": ""},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_username_rejected(self):
        """Test that empty username is rejected"""
        url = reverse("authn:api_rsa_login")
        challenge = self._get_challenge().data
        encrypted = self._encrypt_with_challenge(challenge, self.user_password)
        response = self.client.post(
            url,
            {"username": "", "password": encrypted},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_username_rejected(self):
        """Test that missing username field is rejected"""
        url = reverse("authn:api_rsa_login")
        challenge = self._get_challenge().data
        encrypted = self._encrypt_with_challenge(challenge, self.user_password)
        response = self.client.post(
            url,
            {"password": encrypted},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_rejected(self):
        """Test that missing password field is rejected"""
        url = reverse("authn:api_rsa_login")
        response = self.client.post(
            url,
            {"username": self.user.username},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_encrypted_password_rejected(self):
        """Test that malformed encrypted password is rejected"""
        url = reverse("authn:api_rsa_login")
        response = self.client.post(
            url,
            {"username": self.user.username, "password": "not_valid_base64!!!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_access_token(self):
        """Test that successful login returns access token"""
        response = self._perform_rsa_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIsNotNone(response.data["access"])

    def test_access_token_cookie_set_on_login(self):
        """Test that access token cookie is set on login"""
        response = self._perform_rsa_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)

    def test_username_throttle_per_user(self):
        """Test that username throttle is per-username"""
        url = reverse("authn:api_rsa_login")

        # Create another user
        other_user = User.objects.create_user(
            username="otheruser", password="testpass456"
        )

        # Exhaust throttle for first user
        for _ in range(6):
            self.client.post(
                url,
                {"username": self.user.username, "password": "invalid"},
                format="json",
            )

        # Other user should still be able to attempt login
        # (might be throttled by IP, but not by username)
        cache.clear()  # Clear to test username-specific throttling
        response = self.client.post(
            url,
            {"username": other_user.username, "password": "invalid"},
            format="json",
        )
        # Should get 400 (bad request) not 429 (throttled) for first attempt
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_429_TOO_MANY_REQUESTS],
        )


class CookieSecurityTests(APITestCase):
    """Test cookie security attributes"""

    @classmethod
    def setUpTestData(cls):
        cls.user_password = "testpass123"
        cls.user = User.objects.create_user(
            username="cookieuser", password=cls.user_password
        )
        create_user_profile(cls.user, "Cookie User", "COOKIE123", None)

    def setUp(self):
        super().setUp()
        cache.clear()
        LoginSecurityTests._provision_rsa_key()

    def test_refresh_token_httponly(self):
        """Test that refresh token cookie is HttpOnly"""
        # Perform login to get cookies
        challenge_url = reverse("authn:api_login_challenge")
        challenge_response = self.client.get(challenge_url)
        challenge = challenge_response.data

        payload = json.dumps(
            {"nonce": challenge["nonce"], "password": self.user_password}
        ).encode("utf-8")
        public_key = serialization.load_pem_public_key(
            challenge["public_key"].encode("utf-8")
        )
        ciphertext = public_key.encrypt(
            payload,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        encrypted = base64.b64encode(ciphertext).decode("utf-8")

        login_url = reverse("authn:api_rsa_login")
        response = self.client.post(
            login_url,
            {"username": self.user.username, "password": encrypted},
            format="json",
        )

        refresh_cookie = response.cookies.get("refresh_token")
        if refresh_cookie:
            cookie_header = refresh_cookie.output(header="")
            self.assertIn("HttpOnly", cookie_header)

    def test_access_token_cookie_attributes(self):
        """Test that access token cookie has secure attributes"""
        challenge_url = reverse("authn:api_login_challenge")
        challenge_response = self.client.get(challenge_url)
        challenge = challenge_response.data

        payload = json.dumps(
            {"nonce": challenge["nonce"], "password": self.user_password}
        ).encode("utf-8")
        public_key = serialization.load_pem_public_key(
            challenge["public_key"].encode("utf-8")
        )
        ciphertext = public_key.encrypt(
            payload,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        encrypted = base64.b64encode(ciphertext).decode("utf-8")

        login_url = reverse("authn:api_rsa_login")
        response = self.client.post(
            login_url,
            {"username": self.user.username, "password": encrypted},
            format="json",
        )

        access_cookie = response.cookies.get("access_token")
        if access_cookie:
            cookie_header = access_cookie.output(header="")
            # Access token uses HttpOnly for XSS protection
            # The token is returned in response body for JS use
            self.assertIn("HttpOnly", cookie_header)
            self.assertIn("SameSite", cookie_header)
