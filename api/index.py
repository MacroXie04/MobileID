import os
import sys

# Add Django project to Python path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")

from core.wsgi import application as app  # noqa: E402
