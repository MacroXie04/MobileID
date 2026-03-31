import os
import sys
import traceback

# Add Django project to Python path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")
os.environ.setdefault("STATIC_ROOT", "/tmp/staticfiles")

_startup_error = None

try:
    from core.wsgi import application
except Exception:
    application = None
    _startup_error = traceback.format_exc()


def app(environ, start_response):
    if application is not None:
        return application(environ, start_response)
    body = f"Django startup error:\n{_startup_error}".encode()
    start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
    return [body]
