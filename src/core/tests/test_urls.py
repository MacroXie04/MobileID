"""
Tests for URL configuration and routing.
"""

from django.test import TestCase, override_settings
from django.urls import reverse, resolve


class URLConfigurationTest(TestCase):
    """Test URL configuration and routing"""

    def test_admin_url_resolves(self):
        """Test that admin URL resolves correctly"""
        url = reverse("admin:index")
        resolver_match = resolve(url)
        self.assertEqual(resolver_match.url_name, "index")

    @override_settings(ADMIN_URL_PATH="custom-admin")
    def test_admin_url_uses_custom_path(self):
        """Test that admin URL uses custom path from settings"""
        from django.conf import settings

        url = reverse("admin:index")
        self.assertTrue(url.startswith(f"/{settings.ADMIN_URL_PATH}/"))

    def test_health_check_url_resolves(self):
        """Test that health check URL resolves correctly"""
        url = reverse("health_check")
        self.assertEqual(url, "/health/")
        resolver_match = resolve(url)
        self.assertEqual(resolver_match.url_name, "health_check")

    def test_authn_urls_included(self):
        """Test that authentication URLs are included"""
        # Test login endpoint
        url = reverse("authn:api_token_obtain_pair")
        self.assertEqual(url, "/authn/token/")

        # Test registration endpoint
        url = reverse("authn:api_register")
        self.assertEqual(url, "/authn/register/")

        # Test user info endpoint
        url = reverse("authn:api_user_info")
        self.assertEqual(url, "/authn/user_info/")

    def test_index_urls_included(self):
        """Test that index URLs are included"""
        # Test barcode generation endpoint
        url = reverse("index:api_generate_barcode")
        self.assertEqual(url, "/generate_barcode/")

        # Test dashboard endpoint
        url = reverse("index:api_barcode_dashboard")
        self.assertEqual(url, "/barcode_dashboard/")

    def test_static_files_configuration(self):
        """Test static files are properly configured in DEBUG mode"""
        with override_settings(DEBUG=True):
            from django.conf.urls.static import static
            from django.conf import settings

            static_urls = static(
                settings.STATIC_URL, document_root=settings.STATIC_ROOT
            )
            self.assertIsNotNone(static_urls)
