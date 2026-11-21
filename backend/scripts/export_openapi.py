"""Export the FastAPI OpenAPI schema to stdout.

Usage (from backend/):
    python scripts/export_openapi.py --output ../contracts/openapi.json

The CI pipeline uses this to verify that contracts/openapi.json is current.
Never edit contracts/openapi.json manually — always regenerate from FastAPI.
"""

import argparse
import json
import sys
from pathlib import Path

from app.core.config import Settings
from app.main import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the FastAPI OpenAPI schema.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write UTF-8 JSON to this path instead of stdout.",
    )
    args = parser.parse_args()

    schema = create_app(Settings(environment="local")).openapi()
    serialized = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(serialized)


if __name__ == "__main__":
    main()
