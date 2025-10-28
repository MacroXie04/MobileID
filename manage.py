#!/usr/bin/env python
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # Ensure src/ is on the path so we can import the Django project
    project_root = Path(__file__).resolve().parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mobileid.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
