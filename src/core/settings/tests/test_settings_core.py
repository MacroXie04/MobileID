"""
Tests for Django settings configuration — core settings.
"""

from django.conf import settings
from django.test import TestCase


class SettingsConfigurationTest(TestCase):
    """Test Django settings configuration"""

    def test_secret_key_configuration(self):
        """Test that SECRET_KEY is properly configured"""
        self.assertIsNotNone(settings.SECRET_KEY)
        # In tests, SECRET_KEY should be set even if not in environment

    def test_installed_apps_configuration(self):
        """Test that all required apps are installed"""
        required_apps = [
            "index.apps.IndexConfig",
            "authn.apps.AuthnConfig",
            "rest_framework",
            "rest_framework_simplejwt",
            "corsheaders",
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
        ]

        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_middleware_configuration(self):
        """Test that middleware is properly configured"""
        required_middleware = [
            "corsheaders.middleware.CorsMiddleware",
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ]

        for middleware in required_middleware:
            self.assertIn(middleware, settings.MIDDLEWARE)

    def test_database_configuration(self):
        """Test database configuration"""
        self.assertIn("default", settings.DATABASES)
        default_db = settings.DATABASES["default"]
        self.assertIn("ENGINE", default_db)
        self.assertIn("NAME", default_db)

    def test_rest_framework_configuration(self):
        """Test REST framework configuration"""
        self.assertIn("DEFAULT_AUTHENTICATION_CLASSES", settings.REST_FRAMEWORK)
        self.assertIn("DEFAULT_PERMISSION_CLASSES", settings.REST_FRAMEWORK)

        # Check authentication classes
        auth_classes = settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
        self.assertIn(
            "authn.authentication.CookieJWTAuthentication",
            auth_classes,
        )
        self.assertIn(
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            auth_classes,
        )

    def test_jwt_configuration(self):
        """Test JWT configuration"""
        self.assertIn("ACCESS_TOKEN_LIFETIME", settings.SIMPLE_JWT)
        self.assertIn("REFRESH_TOKEN_LIFETIME", settings.SIMPLE_JWT)
        self.assertIn("ALGORITHM", settings.SIMPLE_JWT)

        # Check that tokens have appropriate lifetime
        access_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        # Tests always run with TESTING=True → 1-day access tokens
        self.assertEqual(access_lifetime.days, 1)

    def test_cors_configuration(self):
        """Test CORS configuration"""
        self.assertIsNotNone(settings.CORS_ALLOWED_ORIGINS)
        self.assertTrue(settings.CORS_ALLOW_CREDENTIALS)

        # Check that local development origins are allowed
        expected_origins = [
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

        for origin in expected_origins:
            self.assertIn(origin, settings.CORS_ALLOWED_ORIGINS)

    def test_static_files_configuration(self):
        """Test static files configuration"""
        self.assertEqual(settings.STATIC_URL, "/static/")
        self.assertIsNotNone(settings.STATIC_ROOT)

    def test_time_zone_configuration(self):
        """Test timezone configuration"""
        self.assertEqual(settings.TIME_ZONE, "America/Los_Angeles")
        self.assertTrue(settings.USE_TZ)

    def test_session_configuration(self):
        """Test session configuration"""
        self.assertEqual(settings.SESSION_COOKIE_AGE, 2592000)  # 30 days
        self.assertFalse(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertFalse(settings.SESSION_SAVE_EVERY_REQUEST)
