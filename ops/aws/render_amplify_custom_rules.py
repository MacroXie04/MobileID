#!/usr/bin/env python3
"""
Render Amplify custom rewrite rules with the current backend origin.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

PLACEHOLDER = "__BACKEND_ORIGIN__"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backend_origin = os.environ["BACKEND_ORIGIN"].rstrip("/")

    template_path = Path(args.template)
    output_path = Path(args.output)

    template = template_path.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise ValueError(f"Missing placeholder {PLACEHOLDER} in {template_path}")

    rendered = template.replace(PLACEHOLDER, backend_origin)
    json.loads(rendered)
    output_path.write_text(f"{rendered}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
