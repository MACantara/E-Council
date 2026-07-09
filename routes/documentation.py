"""
Documentation routes blueprint for E-Council.
Contains all routes related to documentation management.
"""

from datetime import datetime

import cloudinary
import cloudinary.uploader
import pandas as pd
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from models import (
    ActivityReportForms,
    ConceptPaperForms,
    Documentation,
    Events,
    LearningJournalForms,
    Signatories,
    Users,
    db,
)
from utils.auth import belongs_to_user_or_department, is_admin

# Import helper function from utils
from utils.helpers import allowed_image_file

# Create blueprint
documentation_bp = Blueprint("documentation", __name__, url_prefix="/documentation")


@documentation_bp.route("/documentation-overview")
@login_required
def documentation_overview():
    # Query for all documentation with concept paper subject, ordered by academic year (desc) and semester
    query = (
        db.session.query(Documentation, ConceptPaperForms.concept_paper_forms_subject)
        .outerjoin(
            ActivityReportForms,
            Documentation.documentation_activity_report_forms_id == ActivityReportForms.activity_report_forms_id,
        )
        .outerjoin(
            LearningJournalForms,
            Documentation.documentation_learning_journal_forms_id == LearningJournalForms.learning_journal_forms_id,
        )
        .outerjoin(
            ConceptPaperForms,
            db.or_(
                ActivityReportForms.activity_report_forms_concept_paper_forms_id
                == ConceptPaperForms.concept_paper_forms_id,
                LearningJournalForms.learning_journal_forms_concept_paper_forms_id
                == ConceptPaperForms.concept_paper_forms_id,
            ),
        )
        .order_by(Documentation.documentation_academic_year.desc(), Documentation.documentation_semester.desc())
    )

    # Admins can view all documentation; others only see their own department's or ones they prepared
    if not is_admin(current_user):
        query = query.filter(
            or_(
                Documentation.documentation_departments_id == current_user.users_departments_id,
                Documentation.documentation_prepared_by == current_user.users_id,
            )
        )

    documentations = query.all()

    return render_template(
        "documentation/documentation-overview.html", documentations=documentations, sort_by_date="recent-to-old"
    )


@documentation_bp.route("/add-documentation", methods=["GET", "POST"])
@login_required
def add_documentation():
    if request.method == "POST":
        documentation_events_id = request.form.get("documentation-events-id")
        documentation_status = request.form.get("documentation-status")
        documentation_type = request.form.get("documentation-type")
        documentation_activity_report_forms_id = request.form.get("documentation-activity-report-forms-id")
        documentation_prepared_by = request.form.get("documentation-prepared-by")
        documentation_learning_journal_forms_id = request.form.get("documentation-learning-journal-forms-id")
        documentation_noted_by = request.form.get("documentation-noted-by")
        documentation_date_of_submission = request.form.get("documentation-date-of-submission")
        documentation_checked_by = request.form.get("learning-journal-forms-checked-by")
        documentation_rating = request.form.get("documentation-rating")
        documentation_comments_suggestions = request.form.get("documentation-comments-suggestions")

        # Retrieve activity strengths, weaknesses, and recommendations
        activity_strengths = request.form.getlist("activity-strengths")
        activity_weaknesses = request.form.getlist("activity-weaknesses")
        activity_recommendations = request.form.getlist("activity-recommendations")

        # Get Learning Journal Form fields
        learning_journal_forms_name_of_student = request.form.get("learning-journal-forms-name-of-student")
        learning_journal_forms_course_year_level = request.form.get("learning-journal-forms-course-year-level")
        learning_journal_forms_id_number = request.form.get("learning-journal-forms-id-number")
        learning_journal_forms_overall_reflection = request.form.get("learning-journal-forms-overall-reflection")
        learning_journal_forms_prepared_by = request.form.get("learning-journal-forms-prepared-by")
        learning_journal_forms_seen_and_read_by = request.form.get("learning-journal-forms-seen-and-read-by")

        # Retrieve event details using documentation_events_id
        event = Events.query.get(documentation_events_id)
        if event:
            documentation_academic_year = event.events_academic_year
            documentation_semester = event.events_semester
            concept_paper_id = event.events_concept_paper_forms_id

            # Get the learning journal form linked to the concept paper
            concept_paper_learning_journal = LearningJournalForms.query.filter_by(
                learning_journal_forms_concept_paper_forms_id=concept_paper_id
            ).first()

        # Convert date fields to datetime objects
        documentation_date_of_submission = datetime.strptime(documentation_date_of_submission, "%Y-%m-%d")

        # Update learning journal form details if it exists
        if (
            concept_paper_learning_journal
            and learning_journal_forms_name_of_student
            and learning_journal_forms_course_year_level
        ):
            concept_paper_learning_journal.learning_journal_forms_name_of_student = (
                learning_journal_forms_name_of_student
            )
            concept_paper_learning_journal.learning_journal_forms_course_year_level = (
                learning_journal_forms_course_year_level
            )
            concept_paper_learning_journal.learning_journal_forms_id_number = learning_journal_forms_id_number
            concept_paper_learning_journal.learning_journal_forms_overall_reflection = (
                learning_journal_forms_overall_reflection
            )
            concept_paper_learning_journal.learning_journal_forms_prepared_by = learning_journal_forms_prepared_by
            concept_paper_learning_journal.learning_journal_forms_seen_and_read_by = (
                learning_journal_forms_seen_and_read_by
            )

        # Build JSON lists from form data
        activity_strengths = [s for s in activity_strengths if s]
        activity_weaknesses = [w for w in activity_weaknesses if w]
        activity_recommendations = [r for r in activity_recommendations if r]

        # Update learning journal observations and learnings as JSON lists
        if concept_paper_learning_journal:
            concept_paper_learning_journal.learnings = [
                learning for learning in request.form.getlist("learnings") if learning.strip()
            ]
            concept_paper_learning_journal.observations = [o for o in request.form.getlist("observations") if o.strip()]

        # Build tally items JSON list
        tally_items_names = request.form.getlist("tally-items-name[]")
        tally_items_extremely_satisfied = request.form.getlist("tally-items-extremely-satisfied-rating-total[]")
        tally_items_satisfied = request.form.getlist("tally-items-satisfied-rating-total[]")
        tally_items_neutral = request.form.getlist("tally-items-neutral-rating-total[]")
        tally_items_dissatisfied = request.form.getlist("tally-items-dissatisfied-rating-total[]")
        tally_items_extremely_dissatisfied = request.form.getlist("tally-items-extremely-dissatisfied-rating-total[]")
        tally_items = []
        for i in range(len(tally_items_names)):
            if tally_items_names[i].strip():
                tally_items.append(
                    {
                        "name": tally_items_names[i],
                        "extremely_satisfied": int(tally_items_extremely_satisfied[i]),
                        "satisfied": int(tally_items_satisfied[i]),
                        "neutral": int(tally_items_neutral[i]),
                        "dissatisfied": int(tally_items_dissatisfied[i]),
                        "extremely_dissatisfied": int(tally_items_extremely_dissatisfied[i]),
                    }
                )

        # Build evaluation images JSON list
        evaluation_images = []
        for image in request.files.getlist("evaluation-images[]"):
            if image and allowed_image_file(image.filename):
                try:
                    upload_result = cloudinary.uploader.upload(
                        image, folder="results_of_the_evaluation_images", resource_type="auto"
                    )
                    evaluation_images.append(
                        {"url": upload_result["secure_url"], "public_id": upload_result["public_id"]}
                    )
                except Exception as e:
                    current_app.logger.error("Failed to upload evaluation image: %s", e, exc_info=True)
                    flash(f"Failed to upload evaluation image: {str(e)}", "error")

        # Build attendance images JSON list
        attendance_images = []
        for image in request.files.getlist("attendance-images[]"):
            if image and allowed_image_file(image.filename):
                try:
                    upload_result = cloudinary.uploader.upload(
                        image, folder="summary_of_attendance_images", resource_type="auto"
                    )
                    attendance_images.append(
                        {"url": upload_result["secure_url"], "public_id": upload_result["public_id"]}
                    )
                except Exception as e:
                    current_app.logger.error("Failed to upload attendance image: %s", e, exc_info=True)
                    flash(f"Failed to upload attendance image: {str(e)}", "error")

        # Build event photo documentation images JSON list
        event_photo_images = []
        for image in request.files.getlist("photo-documentation-images[]"):
            if image and allowed_image_file(image.filename):
                try:
                    upload_result = cloudinary.uploader.upload(
                        image, folder="event_photo_documentation_images", resource_type="auto"
                    )
                    event_photo_images.append(
                        {"url": upload_result["secure_url"], "public_id": upload_result["public_id"]}
                    )
                except Exception as e:
                    current_app.logger.error("Failed to upload event photo documentation image: %s", e, exc_info=True)
                    flash(f"Failed to upload event photo documentation image: {str(e)}", "error")

        # Build evaluation student names JSON list from Excel file
        evaluation_student_names = []
        if "student-list-excel" in request.files:
            file = request.files["student-list-excel"]
            if file and file.filename.endswith(".xlsx"):
                try:
                    df = pd.read_excel(file)
                    name_column = None
                    for col in df.columns:
                        if "full name" in col.lower():
                            name_column = col
                            break

                    if name_column:
                        evaluation_student_names = df[name_column].dropna().tolist()
                except Exception as e:
                    current_app.logger.error("Failed to process student list: %s", e, exc_info=True)
                    flash(f"Failed to process student list: {str(e)}", "error")

        # Create a new documentation entry with JSON fields
        new_documentation = Documentation(
            documentation_events_id=documentation_events_id,
            documentation_academic_year=documentation_academic_year,
            documentation_semester=documentation_semester,
            documentation_status=documentation_status,
            documentation_departments_id=current_user.users_departments_id,
            documentation_type=documentation_type,
            documentation_activity_report_forms_id=documentation_activity_report_forms_id,
            documentation_prepared_by=documentation_prepared_by,
            documentation_learning_journal_forms_id=documentation_learning_journal_forms_id,
            documentation_checked_by=documentation_checked_by,
            documentation_noted_by=documentation_noted_by,
            documentation_date_of_submission=documentation_date_of_submission,
            documentation_rating=documentation_rating,
            documentation_comments_suggestions=documentation_comments_suggestions,
            activity_strengths=activity_strengths,
            activity_weaknesses=activity_weaknesses,
            activity_recommendations=activity_recommendations,
            tally_items=tally_items,
            evaluation_images=evaluation_images,
            attendance_images=attendance_images,
            event_photo_images=event_photo_images,
            evaluation_student_names=evaluation_student_names,
            evaluation_forms=[],
        )

        db.session.add(new_documentation)
        db.session.commit()
        flash("Documentation added successfully!", "success")
        return redirect(url_for("documentation.documentation_overview"))

    # Query for events
    events = Events.query.all()

    # Query for distinct academic years
    academic_years = db.session.query(Documentation.documentation_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for users
    users = Users.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    # Query for activity report forms and include related events
    activity_reports = (
        db.session.query(ActivityReportForms)
        .join(
            Events,
            ActivityReportForms.activity_report_forms_concept_paper_forms_id == Events.events_concept_paper_forms_id,
        )
        .all()
    )

    # Query for learning journal forms and include related events
    learning_journals = (
        db.session.query(LearningJournalForms)
        .join(
            Events,
            LearningJournalForms.learning_journal_forms_concept_paper_forms_id == Events.events_concept_paper_forms_id,
        )
        .all()
    )

    return render_template(
        "documentation/add-documentation.html",
        events=events,
        academic_years=academic_years,
        users=users,
        signatories=signatories,
        activity_reports=activity_reports,
        learning_journals=learning_journals,
    )


@documentation_bp.route("/update-documentation-status/<int:documentation_id>", methods=["POST"])
@login_required
def update_documentation_status(documentation_id):
    data = request.get_json()
    new_status = data.get("status")

    # Find the documentation by ID
    documentation = Documentation.query.get_or_404(documentation_id)

    if not belongs_to_user_or_department(documentation, current_user):
        abort(403)

    # Update the documentation status
    documentation.documentation_status = new_status
    db.session.commit()

    return jsonify(success=True)


@documentation_bp.route("/update-documentation/<int:documentation_id>", methods=["GET", "POST"])
@login_required
def update_documentation(documentation_id):
    documentation = Documentation.query.get_or_404(documentation_id)

    if not belongs_to_user_or_department(documentation, current_user):
        abort(403)

    # Get or create learning journal
    learning_journal = None
    if documentation.documentation_learning_journal_forms_id:
        learning_journal = LearningJournalForms.query.get(documentation.documentation_learning_journal_forms_id)
    else:
        learning_journal = LearningJournalForms()
        db.session.add(learning_journal)
        documentation.documentation_learning_journal_forms_id = learning_journal.learning_journal_forms_id

    if request.method == "POST":
        documentation_events_id = request.form.get("documentation-events-id")
        documentation_academic_year = request.form.get("documentation-academic-year")
        other_academic_year = request.form.get("other-academic-year")
        documentation_semester = request.form.get("documentation-semester")
        documentation_status = request.form.get("documentation-status")
        documentation_type = request.form.get("documentation-type")
        documentation_activity_report_forms_id = request.form.get("documentation-activity-report-forms-id")
        documentation_prepared_by = request.form.get("documentation-prepared-by")
        documentation_learning_journal_forms_id = request.form.get("documentation-learning-journal-forms-id")
        documentation_checked_by = request.form.get("documentation-checked-by")
        documentation_noted_by = request.form.get("documentation-noted-by")
        documentation_date_of_submission = request.form.get("documentation-date-of-submission")

        # Use the value from the additional input field if "Other A.Y." is selected
        if documentation_academic_year == "Other":
            documentation_academic_year = other_academic_year

        # Convert date fields to datetime objects
        documentation_date_of_submission = datetime.strptime(documentation_date_of_submission, "%Y-%m-%d")

        # Update the documentation entry
        documentation.documentation_events_id = documentation_events_id
        documentation.documentation_academic_year = documentation_academic_year
        documentation.documentation_semester = documentation_semester
        documentation.documentation_status = documentation_status
        documentation.documentation_type = documentation_type
        documentation.documentation_activity_report_forms_id = documentation_activity_report_forms_id
        documentation.documentation_prepared_by = documentation_prepared_by
        documentation.documentation_learning_journal_forms_id = documentation_learning_journal_forms_id
        documentation.documentation_checked_by = documentation_checked_by
        documentation.documentation_noted_by = documentation_noted_by
        documentation.documentation_date_of_submission = documentation_date_of_submission

        # Update strengths, weaknesses, and recommendations as JSON lists
        documentation.activity_strengths = [
            s.strip() for s in request.form.getlist("activity-strengths[]") if s.strip()
        ]
        documentation.activity_weaknesses = [
            w.strip() for w in request.form.getlist("activity-weaknesses[]") if w.strip()
        ]
        documentation.activity_recommendations = [
            r.strip() for r in request.form.getlist("activity-recommendations[]") if r.strip()
        ]

        # Update Learning Journal fields
        learning_journal.learning_journal_forms_name_of_student = request.form.get(
            "learning-journal-forms-name-of-student"
        )
        learning_journal.learning_journal_forms_course_year_level = request.form.get(
            "learning-journal-forms-course-year-level"
        )
        learning_journal.learning_journal_forms_id_number = request.form.get("learning-journal-forms-id-number")
        learning_journal.learning_journal_forms_overall_reflection = request.form.get(
            "learning-journal-forms-overall-reflection"
        )
        learning_journal.learning_journal_forms_seen_and_read_by = request.form.get(
            "learning-journal-forms-seen-and-read-by"
        )
        learning_journal.learning_journal_forms_prepared_by = request.form.get("learning-journal-forms-prepared-by")
        learning_journal.learning_journal_forms_checked_by = request.form.get("learning-journal-forms-checked-by")

        # Update learnings and observations as JSON lists
        learning_journal.learnings = [
            learning.strip() for learning in request.form.getlist("learnings[]") if learning.strip()
        ]
        learning_journal.observations = [o.strip() for o in request.form.getlist("observations[]") if o.strip()]

        # Handle evaluation images (delete removed, then append new uploads)
        evaluation_images = documentation.evaluation_images or []
        deleted_image_ids = request.form.get("deleted_evaluation_images", "").split(",")
        if deleted_image_ids and deleted_image_ids[0]:
            deleted_ids = {img_id.strip() for img_id in deleted_image_ids if img_id.strip()}
            filtered_images = []
            for image in evaluation_images:
                if image.get("public_id") in deleted_ids or image.get("url") in deleted_ids:
                    try:
                        cloudinary.uploader.destroy(image["public_id"])
                    except Exception as e:
                        current_app.logger.error("Error deleting some evaluation images: %s", e, exc_info=True)
                        flash("Error deleting some evaluation images", "error")
                else:
                    filtered_images.append(image)
            evaluation_images = filtered_images

        for image in request.files.getlist("evaluation-images[]"):
            if image and allowed_image_file(image.filename):
                try:
                    upload_result = cloudinary.uploader.upload(image)
                    evaluation_images.append(
                        {"url": upload_result["secure_url"], "public_id": upload_result["public_id"]}
                    )
                except Exception as e:
                    current_app.logger.error("Error uploading some evaluation images: %s", e, exc_info=True)
                    flash("Error uploading some evaluation images", "error")
        documentation.evaluation_images = evaluation_images

        # Handle attendance images
        attendance_images = documentation.attendance_images or []
        deleted_attendance_image_ids = request.form.get("deleted_attendance_images", "").split(",")
        if deleted_attendance_image_ids and deleted_attendance_image_ids[0]:
            deleted_ids = {img_id.strip() for img_id in deleted_attendance_image_ids if img_id.strip()}
            filtered_images = []
            for image in attendance_images:
                if image.get("public_id") in deleted_ids or image.get("url") in deleted_ids:
                    try:
                        cloudinary.uploader.destroy(image["public_id"])
                    except Exception as e:
                        current_app.logger.error("Error deleting some attendance images: %s", e, exc_info=True)
                        flash("Error deleting some attendance images", "error")
                else:
                    filtered_images.append(image)
            attendance_images = filtered_images

        for image in request.files.getlist("attendance-images[]"):
            if image and allowed_image_file(image.filename):
                try:
                    upload_result = cloudinary.uploader.upload(image)
                    attendance_images.append(
                        {"url": upload_result["secure_url"], "public_id": upload_result["public_id"]}
                    )
                except Exception as e:
                    current_app.logger.error("Error uploading some attendance images: %s", e, exc_info=True)
                    flash("Error uploading some attendance images", "error")
        documentation.attendance_images = attendance_images

        # Handle photo documentation images
        event_photo_images = documentation.event_photo_images or []
        deleted_photo_doc_image_ids = request.form.get("deleted_photo_doc_images", "").split(",")
        if deleted_photo_doc_image_ids and deleted_photo_doc_image_ids[0]:
            deleted_ids = {img_id.strip() for img_id in deleted_photo_doc_image_ids if img_id.strip()}
            filtered_images = []
            for image in event_photo_images:
                if image.get("public_id") in deleted_ids or image.get("url") in deleted_ids:
                    try:
                        cloudinary.uploader.destroy(image["public_id"])
                    except Exception as e:
                        current_app.logger.error("Error deleting some photo documentation images: %s", e, exc_info=True)
                        flash("Error deleting some photo documentation images", "error")
                else:
                    filtered_images.append(image)
            event_photo_images = filtered_images

        for image in request.files.getlist("photo-documentation-images[]"):
            if image and allowed_image_file(image.filename):
                try:
                    upload_result = cloudinary.uploader.upload(image)
                    event_photo_images.append(
                        {"url": upload_result["secure_url"], "public_id": upload_result["public_id"]}
                    )
                except Exception as e:
                    current_app.logger.error("Error uploading some photo documentation images: %s", e, exc_info=True)
                    flash("Error uploading some photo documentation images", "error")
        documentation.event_photo_images = event_photo_images

        # Update tally items as a JSON list
        tally_items_names = request.form.getlist("tally-items-name[]")
        tally_items_extremely_satisfied = request.form.getlist("tally-items-extremely-satisfied-rating-total[]")
        tally_items_satisfied = request.form.getlist("tally-items-satisfied-rating-total[]")
        tally_items_neutral = request.form.getlist("tally-items-neutral-rating-total[]")
        tally_items_dissatisfied = request.form.getlist("tally-items-dissatisfied-rating-total[]")
        tally_items_extremely_dissatisfied = request.form.getlist("tally-items-extremely-dissatisfied-rating-total[]")

        tally_items = []
        for i in range(len(tally_items_names)):
            if tally_items_names[i].strip():
                tally_items.append(
                    {
                        "name": tally_items_names[i],
                        "extremely_satisfied": int(tally_items_extremely_satisfied[i]),
                        "satisfied": int(tally_items_satisfied[i]),
                        "neutral": int(tally_items_neutral[i]),
                        "dissatisfied": int(tally_items_dissatisfied[i]),
                        "extremely_dissatisfied": int(tally_items_extremely_dissatisfied[i]),
                    }
                )
        documentation.tally_items = tally_items

        # Update evaluation forms as a JSON list
        evaluation_form_names = request.form.getlist("evaluation-form-name[]")
        evaluation_form_ratings = request.form.getlist("evaluation-form-rating[]")

        evaluation_forms = []
        for i in range(len(evaluation_form_names)):
            if evaluation_form_names[i].strip():
                rating = evaluation_form_ratings[i] if i < len(evaluation_form_ratings) else None
                evaluation_forms.append({"name": evaluation_form_names[i], "rating": rating})
        documentation.evaluation_forms = evaluation_forms

        # Update student list as a JSON list
        documentation.evaluation_student_names = [
            s.strip() for s in request.form.getlist("student-names[]") if s.strip()
        ]

        db.session.commit()
        flash("Documentation updated successfully!", "success")
        return redirect(url_for("documentation.documentation_overview"))

    # Query for events
    events = Events.query.all()

    # Query for distinct academic years
    academic_years = db.session.query(Documentation.documentation_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for users
    users = Users.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    # Query for activity report forms with concept paper subject
    activity_reports = (
        db.session.query(ActivityReportForms, ConceptPaperForms.concept_paper_forms_subject)
        .join(
            ConceptPaperForms,
            ActivityReportForms.activity_report_forms_concept_paper_forms_id
            == ConceptPaperForms.concept_paper_forms_id,
        )
        .all()
    )

    # Prepare activity reports data
    activity_reports_data = [
        {
            "activity_report_forms_id": report.ActivityReportForms.activity_report_forms_id,
            "events_name": report.concept_paper_forms_subject,
        }
        for report in activity_reports
    ]

    # Query for learning journal forms with concept paper subject
    learning_journals = (
        db.session.query(LearningJournalForms, ConceptPaperForms.concept_paper_forms_subject)
        .join(
            ConceptPaperForms,
            LearningJournalForms.learning_journal_forms_concept_paper_forms_id
            == ConceptPaperForms.concept_paper_forms_id,
        )
        .all()
    )

    # Prepare learning journals data
    learning_journals_data = [
        {
            "learning_journal_forms_id": journal.LearningJournalForms.learning_journal_forms_id,
            "events_name": journal.concept_paper_forms_subject,
            "learning_journal_forms_name_of_student": journal.LearningJournalForms.learning_journal_forms_name_of_student,
            "learning_journal_forms_course_year_level": journal.LearningJournalForms.learning_journal_forms_course_year_level,
            "learning_journal_forms_id_number": journal.LearningJournalForms.learning_journal_forms_id_number,
            "learning_journal_forms_date": journal.LearningJournalForms.learning_journal_forms_date,
            "learning_journal_forms_overall_reflection": journal.LearningJournalForms.learning_journal_forms_overall_reflection,
            "learning_journal_forms_prepared_by": journal.LearningJournalForms.learning_journal_forms_prepared_by,
            "learning_journal_forms_seen_and_read_by": journal.LearningJournalForms.learning_journal_forms_seen_and_read_by,
            "learning_journal_forms_checked_by": journal.LearningJournalForms.learning_journal_forms_checked_by,
        }
        for journal in learning_journals
    ]

    # Get learning journal for learnings and observations
    learning_journal = None
    if documentation.documentation_learning_journal_forms_id:
        learning_journal = LearningJournalForms.query.get(documentation.documentation_learning_journal_forms_id)

    # Use JSON fields directly
    tally_items = documentation.tally_items or []
    evaluation_images = documentation.evaluation_images or []
    attendance_images = documentation.attendance_images or []
    photo_doc_images = documentation.event_photo_images or []
    evaluation_forms = documentation.evaluation_forms or []
    evaluation_student_list = documentation.evaluation_student_names or []
    learnings = learning_journal.learnings if learning_journal else []
    observations = learning_journal.observations if learning_journal else []
    strengths = documentation.activity_strengths or []
    weaknesses = documentation.activity_weaknesses or []
    recommendations = documentation.activity_recommendations or []

    return render_template(
        "documentation/update-documentation.html",
        documentation=documentation,
        learning_journal=learning_journal,
        events=events,
        academic_years=academic_years,
        users=users,
        signatories=signatories,
        activity_reports=activity_reports_data,
        learning_journals=learning_journals_data,
        tally_items=tally_items,
        evaluation_images=evaluation_images,
        attendance_images=attendance_images,
        photo_doc_images=photo_doc_images,
        evaluation_student_list=evaluation_student_list,
        evaluation_forms=evaluation_forms,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        learnings=learnings,
        observations=observations,
    )


@documentation_bp.route("/delete-documentation/<int:documentation_id>", methods=["GET", "POST"])
@login_required
def delete_documentation(documentation_id):
    documentation = Documentation.query.get_or_404(documentation_id)

    if not belongs_to_user_or_department(documentation, current_user):
        abort(403)

    if request.method == "POST":
        try:
            # Delete associated images from Cloudinary
            for image in documentation.evaluation_images or []:
                try:
                    if image.get("public_id"):
                        cloudinary.uploader.destroy(image["public_id"], resource_type="image")
                except Exception as e:
                    current_app.logger.error("Error deleting some evaluation images: %s", e, exc_info=True)
                    flash("Error deleting some evaluation images", "error")

            for image in documentation.attendance_images or []:
                try:
                    if image.get("public_id"):
                        cloudinary.uploader.destroy(image["public_id"], resource_type="image")
                except Exception as e:
                    current_app.logger.error("Error deleting some attendance images: %s", e, exc_info=True)
                    flash("Error deleting some attendance images", "error")

            for image in documentation.event_photo_images or []:
                try:
                    if image.get("public_id"):
                        cloudinary.uploader.destroy(image["public_id"], resource_type="image")
                except Exception as e:
                    current_app.logger.error(
                        "Error deleting some event photo documentation images: %s", e, exc_info=True
                    )
                    flash("Error deleting some event photo documentation images", "error")

            # Delete the documentation entry (JSON data is removed automatically with the record)
            db.session.delete(documentation)
            db.session.commit()

            flash("Documentation deleted successfully!", "success")
            return redirect(url_for("documentation.documentation_overview"))
        except Exception as e:
            current_app.logger.error("Failed to delete documentation: %s", e, exc_info=True)
            db.session.rollback()
            flash("Failed to delete documentation.", "error")

    return render_template("documentation/delete-documentation.html", documentation=documentation)


@documentation_bp.route("/get-related-forms/<int:event_id>", methods=["GET"])
@login_required
def get_related_forms(event_id):
    # Query for the concept paper form ID related to the event
    concept_paper_form_id = (
        db.session.query(Events.events_concept_paper_forms_id).filter(Events.events_id == event_id).scalar()
    )

    # Query for activity report forms related to the concept paper form
    activity_reports = (
        db.session.query(ActivityReportForms)
        .filter(ActivityReportForms.activity_report_forms_concept_paper_forms_id == concept_paper_form_id)
        .all()
    )

    # Query for learning journal forms related to the concept paper form
    learning_journals = (
        db.session.query(LearningJournalForms)
        .filter(LearningJournalForms.learning_journal_forms_concept_paper_forms_id == concept_paper_form_id)
        .all()
    )

    # Get unique signatory IDs from learning_journal_forms_checked_by
    checked_by_ids = set()
    for journal in learning_journals:
        if journal.learning_journal_forms_checked_by:
            checked_by_ids.add(journal.learning_journal_forms_checked_by)

    # Query for filtered signatories
    signatories = db.session.query(Signatories).filter(Signatories.signatory_id.in_(checked_by_ids)).all()

    # Prepare the data to be sent as JSON
    activity_reports_data = [
        {
            "activity_report_forms_id": report.activity_report_forms_id,
            "events_name": report.concept_paper_form.concept_paper_forms_subject,
        }
        for report in activity_reports
    ]

    learning_journals_data = [
        {
            "learning_journal_forms_id": journal.learning_journal_forms_id,
            "events_name": journal.concept_paper_form.concept_paper_forms_subject,
            "learning_journal_forms_checked_by": journal.learning_journal_forms_checked_by,
        }
        for journal in learning_journals
    ]

    signatories_data = [
        {
            "signatory_id": signatory.signatory_id,
            "signatory_first_name": signatory.signatory_first_name,
            "signatory_last_name": signatory.signatory_last_name,
            "signatory_position": signatory.signatory_position,
            "signatory_department": signatory.signatory_department,
        }
        for signatory in signatories
    ]

    return jsonify(
        activity_reports=activity_reports_data, learning_journals=learning_journals_data, signatories=signatories_data
    )


@documentation_bp.route("/get-activity-report-details/<int:activity_report_id>", methods=["GET"])
@login_required
def get_activity_report_details(activity_report_id):
    # Get the activity report JSON lists
    activity_report = ActivityReportForms.query.get_or_404(activity_report_id)
    strengths = activity_report.strengths or []
    weaknesses = activity_report.weaknesses or []
    recommendations = activity_report.recommendations or []

    # Prepare the data to be sent as JSON
    strengths_data = [{"activity_strengths_content": content} for content in strengths]
    weaknesses_data = [{"activity_weaknesses_content": content} for content in weaknesses]
    recommendations_data = [{"activity_recommendations_content": content} for content in recommendations]

    return jsonify(strengths=strengths_data, weaknesses=weaknesses_data, recommendations=recommendations_data)


@documentation_bp.route("/process-student-excel", methods=["POST"])
@login_required
def process_student_excel():
    if "excel_file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})

    file = request.files["excel_file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"})

    if not file.filename.endswith(".xlsx"):
        return jsonify({"success": False, "error": "Please upload an Excel (.xlsx) file"})

    try:
        # Read the Excel file
        df = pd.read_excel(file)

        # Find column containing 'full name' (case insensitive)
        name_column = None
        for col in df.columns:
            if "full name" in col.lower():
                name_column = col
                break

        if name_column is None:
            return jsonify({"success": False, "error": 'No column containing "full name" found'})

        # Get student names
        student_names = df[name_column].dropna().tolist()

        return jsonify({"success": True, "students": student_names})

    except Exception as e:
        current_app.logger.error("Failed to process Excel file: %s", e, exc_info=True)
        return jsonify({"success": False, "error": "Failed to process Excel file"})


@documentation_bp.route("/generate-documentation-pdf/<int:documentation_id>")
@login_required
def generate_documentation_pdf(documentation_id):
    """
    Generate PDF documentation for a given documentation ID.

    NOTE: This is a placeholder for the complete PDF generation function.
    The complete implementation is in app.py lines 4517-5787 and is over 1200 lines long.

    The function uses reportlab to generate a comprehensive PDF with:
    - Activity details table
    - Objectives and learning outcomes table
    - Evaluation table (strengths, weaknesses, recommendations)
    - Learning journal sections (progress notes, overall reflection)
    - Tally sheets with ratings
    - Results of the evaluation images
    - Summary of attendance images
    - Evaluation form with ratings
    - Evaluation student list
    - Photo documentation images
    - Multiple signature sections

    NOTE: The function uses the JSON columns on the Documentation, LearningJournalForms
    and ActivityReportForms models for tally items, evaluation data, images, etc.

    TODO: To complete this function:
    2. Copy the complete implementation from app.py lines 4517-5787
    3. Update all url_for calls to use the blueprint prefix (e.g., url_for('documentation.documentation_overview'))
    4. Replace 'app.logger' with current_app.logger or import current_app
    """

    # Authorize access to the documentation record
    documentation = Documentation.query.get_or_404(documentation_id)
    if not belongs_to_user_or_department(documentation, current_user):
        abort(403)

    # For now, return an error indicating the function needs to be completed
    return jsonify(
        {
            "success": False,
            "error": "PDF generation not yet implemented in blueprint. Copy from app.py lines 4517-5787 after creating missing models.",
        }
    ), 501
