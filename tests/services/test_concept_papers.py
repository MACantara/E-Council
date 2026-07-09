"""Unit tests for the concept paper service."""

import json

import pytest
from werkzeug.exceptions import HTTPException

from models import ConceptPaperForms
from services import concept_papers
from tests.factories import ConceptPaperFormsFactory


class TestDeleteConceptPaper:
    def test_get_renders_delete_template(self, app_context, auth_service_context, sample_user):
        paper = ConceptPaperFormsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context():
            response = concept_papers.delete_concept_paper(paper.concept_paper_forms_id)
        assert isinstance(response, str)

    def test_post_deletes_concept_paper(self, app_context, auth_service_context, sample_user):
        paper = ConceptPaperFormsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context(method="POST"):
            response = concept_papers.delete_concept_paper(paper.concept_paper_forms_id)
        assert response.status_code == 302
        assert ConceptPaperForms.query.get(paper.concept_paper_forms_id) is None

    def test_delete_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        paper = ConceptPaperFormsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with pytest.raises(HTTPException), auth_service_context(user=other_user):
            concept_papers.delete_concept_paper(paper.concept_paper_forms_id)


class TestUpdateConceptPaperStatus:
    def test_update_status(self, app_context, auth_service_context, sample_user):
        paper = ConceptPaperFormsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context(
            method="POST",
            data=json.dumps({"status": "Done"}),
            content_type="application/json",
        ):
            response = concept_papers.update_concept_paper_status(paper.concept_paper_forms_id)
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        updated = ConceptPaperForms.query.get(paper.concept_paper_forms_id)
        assert updated.concept_paper_forms_status == "Done"

    def test_update_status_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        paper = ConceptPaperFormsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with (
            pytest.raises(HTTPException),
            auth_service_context(
                method="POST",
                data=json.dumps({"status": "Done"}),
                content_type="application/json",
                user=other_user,
            ),
        ):
            concept_papers.update_concept_paper_status(paper.concept_paper_forms_id)


class TestCreateConceptPaper:
    def test_get_renders_add_template(self, app_context, auth_service_context, sample_user):
        with auth_service_context():
            response = concept_papers.create_concept_paper()
        assert isinstance(response, str)
