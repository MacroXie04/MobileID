"""
Core app configuration.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for core app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core"

    def ready(self):
        """Import signals, checks, and admin registration when app is ready"""
        # Import admin to register models
        import core.admin  # noqa: F401

        # Import system checks (cache backend validation, etc.)
        import core.checks  # noqa: F401

        # Import signals to connect admin login/logout logging
        import core.signals  # noqa: F401
