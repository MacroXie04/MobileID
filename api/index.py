import os
import sys
import traceback

# Add Django project to Python path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")
os.environ.setdefault("STATIC_ROOT", "/tmp/staticfiles")

try:
    from core.wsgi import application

    app = application
except Exception:
    # If Django fails to start (e.g. during build without env vars),
    # provide an error handler so Vercel can still detect the function.
    _error = traceback.format_exc()

    def app(environ, start_response):
        status = "500 Internal Server Error"
        body = f"Django startup error:\n{_error}".encode()
        start_response(status, [("Content-Type", "text/plain")])
        return [body]
