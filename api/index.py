import os
import sys
import subprocess

# Add Django project to Python path
_base = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(_base, "..", "src")
sys.path.insert(0, _src_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")

# On Vercel, the filesystem is read-only except /tmp.
# Run collectstatic to /tmp on cold start so WhiteNoise can serve admin assets.
_static_root = "/tmp/staticfiles"
os.environ.setdefault("STATIC_ROOT", _static_root)

if not os.path.isdir(os.path.join(_static_root, "admin")):
    subprocess.run(
        [sys.executable, "manage.py", "collectstatic", "--noinput"],
        cwd=_src_dir,
        check=True,
    )

from core.wsgi import application as app  # noqa: E402
