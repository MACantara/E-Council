"""
Celery task definitions for E-Council.

Provides background tasks for email, PDF generation, and AI content generation.
When no ``BROKER_URL`` is configured, tasks run synchronously (eager mode) so
local development and the test suite work without Redis.
"""

import os

from celery import Celery, Task
from flask import has_app_context

from services.base import log_action

# Broker configuration from environment. When no broker is configured, tasks run
# in eager/synchronous mode so the app and tests still work without Redis.
broker_url = os.getenv("BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("RESULT_BACKEND", broker_url)
task_always_eager = os.getenv("BROKER_URL") is None


celery_app = Celery(
    "e-council",
    broker=broker_url,
    backend=result_backend,
    include=["tasks", "services.email.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_always_eager=task_always_eager,
    task_ignore_result=False,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)


class ContextTask(Task):
    """Celery task base that ensures a Flask app context is available."""

    abstract = True

    def __call__(self, *args, **kwargs):
        if has_app_context():
            return super().__call__(*args, **kwargs)

        from app import create_app

        app = create_app(os.getenv("FLASK_ENV", "production"))
        with app.app_context():
            return super().__call__(*args, **kwargs)


celery_app.Task = ContextTask


def _get_download_name(response):
    """Parse the download_name from a Flask send_file response."""
    content_disposition = response.headers.get("Content-Disposition", "")
    if "filename=" in content_disposition:
        _, _, filename = content_disposition.partition("filename=")
        return filename.strip('"')
    return "document.pdf"


@celery_app.task(name="tasks.generate_ai_content")
def generate_ai_content(function_name, args):
    """
    Run an AI generation function in the background.

    Args:
        function_name: Name of the function in ``services.ai`` to call.
        args: List of positional arguments.

    Returns:
        dict: A serialized ServiceResult with ``success``, ``data``, and ``error``.
    """
    from services import ai

    result = getattr(ai, function_name)(*args)
    return {"success": result.success, "data": result.data, "error": result.error}


@celery_app.task(name="tasks.generate_pdf", bind=True)
def generate_pdf(self, module_name, function_name, record_id, user_id):
    """
    Generate a PDF in the background and save it for later download.

    The task runs the existing PDF generation function inside a test request
    context with the requesting user logged in, extracts the PDF bytes, writes
    them to ``uploads/pdfs/<task_id>.pdf``, and returns the path.

    Args:
        module_name: Python module where the PDF generator lives.
        function_name: Name of the PDF generator function.
        record_id: Record identifier passed to the generator.
        user_id: User who requested the PDF (used for access checks).

    Returns:
        dict: ``{"path": "...", "download_name": "..."}``.
    """
    import importlib

    from flask import current_app
    from flask_login import login_user

    from models import Users

    module = importlib.import_module(module_name)
    generator = getattr(module, function_name)

    user = Users.query.get(user_id)

    with current_app.test_request_context():
        if user:
            login_user(user)
        response = generator(record_id)

    status_code = 200
    if isinstance(response, tuple):
        response, status_code = response

    if status_code != 200 or response.content_type != "application/pdf":
        return {
            "error": response.get_data(as_text=True),
            "status_code": status_code,
            "content_type": response.content_type or "text/plain",
        }

    response.direct_passthrough = False
    pdf_bytes = response.get_data()
    download_name = _get_download_name(response)

    task_id = self.request.id or "local"
    output_dir = os.path.join("uploads", "pdfs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{task_id}.pdf")
    with open(output_path, "wb") as pdf_file:
        pdf_file.write(pdf_bytes)

    log_action(
        "generate_pdf",
        f"{module_name}.{function_name}",
        record_id,
        {"status": "success", "path": output_path, "download_name": download_name},
    )

    return {"path": output_path, "download_name": download_name}


def run_task(task, *args, **kwargs):
    """
    Run a Celery task eagerly when no broker is configured, otherwise queue it.

    Returns:
        dict with either the completed result (``ready=True``) or the queued
        ``task_id`` (``ready=False``).
    """
    if celery_app.conf.task_always_eager:
        return {"ready": True, "result": task.apply(args=args, kwargs=kwargs).get()}

    async_result = task.delay(*args, **kwargs)
    return {"ready": False, "task_id": async_result.id}
