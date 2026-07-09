"""Unit tests for the documentation service."""

import json

import pytest
from werkzeug.exceptions import HTTPException

from models import Documentation
from services import documentation
from tests.factories import DocumentationFactory, LearningJournalFormsFactory


class TestDeleteDocumentation:
    def test_get_renders_delete_template(self, app_context, auth_service_context, sample_user):
        doc = DocumentationFactory(department=sample_user.department, prepared_by_user=sample_user)
        with auth_service_context():
            response = documentation.delete_documentation(doc.documentation_id)
        assert isinstance(response, str)

    def test_post_deletes_documentation(self, app_context, auth_service_context, sample_user):
        doc = DocumentationFactory(department=sample_user.department, prepared_by_user=sample_user)
        with auth_service_context(method="POST"):
            response = documentation.delete_documentation(doc.documentation_id)
        assert response.status_code == 302
        assert Documentation.query.get(doc.documentation_id) is None

    def test_delete_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        doc = DocumentationFactory(department=sample_user.department, prepared_by_user=sample_user)
        with pytest.raises(HTTPException), auth_service_context(user=other_user):
            documentation.delete_documentation(doc.documentation_id)


class TestUpdateDocumentationStatus:
    def test_update_status(self, app_context, auth_service_context, sample_user):
        doc = DocumentationFactory(department=sample_user.department, prepared_by_user=sample_user)
        with auth_service_context(
            method="POST",
            data=json.dumps({"status": "Done"}),
            content_type="application/json",
        ):
            response = documentation.update_documentation_status(doc.documentation_id)
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        updated = Documentation.query.get(doc.documentation_id)
        assert updated.documentation_status == "Done"

    def test_update_status_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        doc = DocumentationFactory(department=sample_user.department, prepared_by_user=sample_user)
        with (
            pytest.raises(HTTPException),
            auth_service_context(
                method="POST",
                data=json.dumps({"status": "Done"}),
                content_type="application/json",
                user=other_user,
            ),
        ):
            documentation.update_documentation_status(doc.documentation_id)


class TestUpdateDocumentation:
    def test_get_renders_update_template(self, app_context, auth_service_context, sample_user):
        learning_journal = LearningJournalFormsFactory(prepared_by_user=sample_user)
        doc = DocumentationFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
            documentation_learning_journal_forms_id=learning_journal.learning_journal_forms_id,
        )
        with auth_service_context():
            response = documentation.update_documentation(doc.documentation_id)
        assert isinstance(response, str)


class TestGenerateDocumentationPdf:
    def test_returns_not_implemented(self, app_context, auth_service_context, sample_user):
        doc = DocumentationFactory(department=sample_user.department, prepared_by_user=sample_user)
        with auth_service_context():
            response, status_code = documentation.generate_documentation_pdf(doc.documentation_id)
        assert status_code == 501


class TestAddDocumentation:
    def test_get_renders_add_template(self, app_context, auth_service_context, sample_user):
        with auth_service_context():
            response = documentation.add_documentation()
        assert isinstance(response, str)
