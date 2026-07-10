"""Seed the E-Council database with sample users and data.

Run this after applying migrations (``flask db upgrade``) and configuring the
``.env`` file for the target environment.

Examples:
    python seed.py
    python seed.py --force
"""

import argparse
import os
import sys

from app import create_app


def main() -> int:
    """Entry point for the seed script."""
    parser = argparse.ArgumentParser(description="Seed the E-Council database.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even when FLASK_ENV is set to production.",
    )
    args = parser.parse_args()

    env = os.getenv("FLASK_ENV", "development")
    if env == "production" and not args.force:
        print(
            "ERROR: Refusing to seed a production database. "
            "Use --force to override this safety check."
        )
        return 1

    app = create_app(env if env else None)
    with app.app_context():
        from seeds import run_all

        summary = run_all()

    print("Seeded the following sample data:")
    for key, count in summary.items():
        print(f"  {key}: {count}")

    print("\nDemo credentials:")
    for user in [
        ("admin", "admin@example.com"),
        ("officer", "officer@example.com"),
        ("faculty", "faculty@example.com"),
        ("staff", "staff@example.com"),
    ]:
        print(f"  {user[0]} / {user[1]} -> password: DemoPass123!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
