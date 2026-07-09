"""
WSGI entry point for production deployments.

Example usage with gunicorn:
    gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
"""

from app import create_app

application = create_app("production")
