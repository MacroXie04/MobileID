import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

# Add Django project to Python path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")
os.environ.setdefault("STATIC_ROOT", "/tmp/staticfiles")

try:
    from core.wsgi import application as app  # noqa: E402
except Exception as e:
    _error = traceback.format_exc()

    class handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Django startup error:\n{_error}".encode())
