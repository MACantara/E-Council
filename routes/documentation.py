"""
Documentation routes blueprint for E-Council.
Contains all routes related to documentation management.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from io import BytesIO
import cloudinary
import cloudinary.uploader
from datetime import datetime
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_RIGHT

from models import (
    db,
    Documentation,
    ConceptPaperForms,
    ActivityReportForms,
    Events,
    Users,
    Signatories,
    ActivityStrengths,
    ActivityWeaknesses,
    ActivityRecommendations,
    TallyItems,
    ResultsOfTheEvaluationImages,
    SummaryOfAttendanceImages,
    EventPhotoDocumentationImages,
    EvaluationForm,
    EvaluationListOfStudentNames,
    DepartmentsEvents,
    ObjectivesOfTheActivity,
    LearningOutcomes,
    StudentOrganizations
)

# TODO: These models need to be created or imported from the appropriate location:
# - LearningJournalForms
# - Learnings
# - Observations
# - PersonnelInChargeForms
# - ActivityReportFormsActivityStrengths (association table)
# - ActivityReportFormsActivityWeaknesses (association table)
# - ActivityReportFormsActivityRecommendations (association table)

# For now, we'll import them from the main app if they exist there
# This is a temporary workaround until these models are properly extracted
try:
    from app import LearningJournalForms, Learnings, Observations, PersonnelInChargeForms
    from app import ActivityReportFormsActivityStrengths, ActivityReportFormsActivityWeaknesses, ActivityReportFormsActivityRecommendations
except ImportError:
    # If not available, we'll use None and the routes will need to be fixed
    LearningJournalForms = None
    Learnings = None
    Observations = None
    PersonnelInChargeForms = None
    ActivityReportFormsActivityStrengths = None
    ActivityReportFormsActivityWeaknesses = None
    ActivityReportFormsActivityRecommendations = None

# Import helper function from utils
from utils.helpers import allowed_image_file

# Create blueprint
documentation_bp = Blueprint('documentation', __name__, url_prefix='/documentation')


@documentation_bp.route("/documentation-overview")
@login_required
def documentation_overview():
    # Query for all documentation with concept paper subject, ordered by academic year (desc) and semester
    documentations = db.session.query(
        Documentation,
        ConceptPaperForms.concept_paper_forms_subject
    ).outerjoin(
        ActivityReportForms,
        Documentation.documentation_activity_report_forms_id == ActivityReportForms.activity_report_forms_id
    ).outerjoin(
        LearningJournalForms,
        Documentation.documentation_learning_journal_forms_id == LearningJournalForms.learning_journal_forms_id
    ).outerjoin(
        ConceptPaperForms,
        db.or_(
            ActivityReportForms.activity_report_forms_concept_paper_forms_id == ConceptPaperForms.concept_paper_forms_id,
            LearningJournalForms.learning_journal_forms_concept_paper_forms_id == ConceptPaperForms.concept_paper_forms_id
        )
    ).order_by(
        Documentation.documentation_academic_year.desc(),
        Documentation.documentation_semester.desc()
    ).all()

    return render_template("documentation/documentation-overview.html",
                         documentations=documentations,
                         sort_by_date='recent-to-old')


@documentation_bp.route('/add-documentation', methods=['GET', 'POST'])
@login_required
def add_documentation():
    if request.method == 'POST':
        documentation_events_id = request.form.get('documentation-events-id')
        documentation_status = request.form.get('documentation-status')
        documentation_type = request.form.get('documentation-type')
        documentation_activity_report_forms_id = request.form.get('documentation-activity-report-forms-id')
        documentation_prepared_by = request.form.get('documentation-prepared-by')
        documentation_learning_journal_forms_id = request.form.get('documentation-learning-journal-forms-id')
        documentation_noted_by = request.form.get('documentation-noted-by')
        documentation_date_of_submission = request.form.get('documentation-date-of-submission')
        documentation_checked_by = request.form.get('learning-journal-forms-checked-by')
        documentation_rating = request.form.get('documentation-rating')
        documentation_comments_suggestions = request.form.get('documentation-comments-suggestions')

        # Retrieve activity strengths, weaknesses, and recommendations
        activity_strengths = request.form.getlist('activity-strengths')
        activity_weaknesses = request.form.getlist('activity-weaknesses')
        activity_recommendations = request.form.getlist('activity-recommendations')

        # Get Learning Journal Form fields
        learning_journal_forms_name_of_student = request.form.get('learning-journal-forms-name-of-student')
        learning_journal_forms_course_year_level = request.form.get('learning-journal-forms-course-year-level')
        learning_journal_forms_id_number = request.form.get('learning-journal-forms-id-number')
        learning_journal_forms_overall_reflection = request.form.get('learning-journal-forms-overall-reflection')
        learning_journal_forms_prepared_by = request.form.get('learning-journal-forms-prepared-by')
        learning_journal_forms_seen_and_read_by = request.form.get('learning-journal-forms-seen-and-read-by')

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
        documentation_date_of_submission = datetime.strptime(documentation_date_of_submission, '%Y-%m-%d')

        # Update learning journal form details if it exists
        if concept_paper_learning_journal and learning_journal_forms_name_of_student and learning_journal_forms_course_year_level:
            concept_paper_learning_journal.learning_journal_forms_name_of_student = learning_journal_forms_name_of_student
            concept_paper_learning_journal.learning_journal_forms_course_year_level = learning_journal_forms_course_year_level
            concept_paper_learning_journal.learning_journal_forms_id_number = learning_journal_forms_id_number
            concept_paper_learning_journal.learning_journal_forms_overall_reflection = learning_journal_forms_overall_reflection
            concept_paper_learning_journal.learning_journal_forms_prepared_by = learning_journal_forms_prepared_by
            concept_paper_learning_journal.learning_journal_forms_seen_and_read_by = learning_journal_forms_seen_and_read_by
            learning_journal_forms_id = concept_paper_learning_journal.learning_journal_forms_id

        # Create a new documentation entry
        new_documentation = Documentation(
            documentation_events_id=documentation_events_id,
            documentation_academic_year=documentation_academic_year,
            documentation_semester=documentation_semester,
            documentation_status=documentation_status,
            documentation_type=documentation_type,
            documentation_activity_report_forms_id=documentation_activity_report_forms_id,
            documentation_prepared_by=documentation_prepared_by,
            documentation_learning_journal_forms_id=documentation_learning_journal_forms_id,
            documentation_checked_by=documentation_checked_by,
            documentation_noted_by=documentation_noted_by,
            documentation_date_of_submission=documentation_date_of_submission,
            documentation_rating=documentation_rating,
            documentation_comments_suggestions=documentation_comments_suggestions
        )

        # Add the new documentation to the database
        db.session.add(new_documentation)
        db.session.flush()  # Ensure the documentation ID is available
        documentation_id = new_documentation.documentation_id  # Get the documentation ID

        # Add activity strengths
        for strength_content in activity_strengths:
            if strength_content:
                strength = ActivityStrengths(
                    activity_strengths_documentation_id=documentation_id,
                    activity_strengths_content=strength_content
                )
                db.session.add(strength)

        # Add activity weaknesses
        for weakness_content in activity_weaknesses:
            if weakness_content:
                weakness = ActivityWeaknesses(
                    activity_weaknesses_documentation_id=documentation_id,
                    activity_weaknesses_content=weakness_content
                )
                db.session.add(weakness)

        # Add activity recommendations
        for recommendation_content in activity_recommendations:
            if recommendation_content:
                recommendation = ActivityRecommendations(
                    activity_recommendations_documentation_id=documentation_id,
                    activity_recommendations_content=recommendation_content
                )
                db.session.add(recommendation)

        # Get learnings and observations
        learnings = request.form.getlist('learnings')
        observations = request.form.getlist('observations')

        # Add learnings
        for learning_content in learnings:
            if learning_content.strip():  # Only add non-empty learnings
                new_learning = Learnings(
                    learnings_learning_journal_forms_id=learning_journal_forms_id,
                    learnings_content=learning_content
                )
                db.session.add(new_learning)

        # Add observations
        for observation_content in observations:
            if observation_content.strip():  # Only add non-empty observations
                new_observation = Observations(
                    observations_learning_journal_forms_id=learning_journal_forms_id,
                    observations_content=observation_content
                )
                db.session.add(new_observation)

        # Get tally items data
        tally_items_names = request.form.getlist('tally-items-name[]')
        tally_items_extremely_satisfied = request.form.getlist('tally-items-extremely-satisfied-rating-total[]')
        tally_items_satisfied = request.form.getlist('tally-items-satisfied-rating-total[]')
        tally_items_neutral = request.form.getlist('tally-items-neutral-rating-total[]')
        tally_items_dissatisfied = request.form.getlist('tally-items-dissatisfied-rating-total[]')
        tally_items_extremely_dissatisfied = request.form.getlist('tally-items-extremely-dissatisfied-rating-total[]')

        # Add tally items
        for i in range(len(tally_items_names)):
            if tally_items_names[i].strip():  # Only add if name is not empty
                new_tally_item = TallyItems(
                    tally_items_documentation_id=documentation_id,
                    tally_items_name=tally_items_names[i],
                    tally_items_extremely_satisfied_rating_total=int(tally_items_extremely_satisfied[i]),
                    tally_items_satisfied_rating_total=int(tally_items_satisfied[i]),
                    tally_items_neutral_rating_total=int(tally_items_neutral[i]),
                    tally_items_dissatisfied_rating_total=int(tally_items_dissatisfied[i]),
                    tally_items_extremely_dissatisfied_rating_total=int(tally_items_extremely_dissatisfied[i])
                )
                db.session.add(new_tally_item)

        # Handle evaluation images upload
        evaluation_images = request.files.getlist('evaluation-images[]')
        for image in evaluation_images:
            if image and allowed_image_file(image.filename):
                try:
                    # Upload to Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        image,
                        folder="results_of_the_evaluation_images",
                        resource_type="auto"
                    )

                    # Create database entry for the image
                    new_image = ResultsOfTheEvaluationImages(
                        results_of_the_evaluation_images_documentation_id=documentation_id,
                        results_of_the_evaluation_images_cloudinary_url=upload_result['secure_url'],
                        results_of_the_evaluation_images_cloudinary_public_id=upload_result['public_id']
                    )
                    db.session.add(new_image)
                except Exception as e:
                    flash(f"Failed to upload evaluation image: {str(e)}", "error")

        # Handle summary of attendance images upload
        attendance_images = request.files.getlist('attendance-images[]')
        for image in attendance_images:
            if image and allowed_image_file(image.filename):
                try:
                    # Upload to Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        image,
                        folder="summary_of_attendance_images",
                        resource_type="auto"
                    )

                    # Create database entry for the image
                    new_image = SummaryOfAttendanceImages(
                        summary_of_attendance_images_documentation_id=documentation_id,
                        summary_of_attendance_images_cloudinary_url=upload_result['secure_url'],
                        summary_of_attendance_images_cloudinary_public_id=upload_result['public_id']
                    )
                    db.session.add(new_image)
                except Exception as e:
                    flash(f"Failed to upload attendance image: {str(e)}", "error")

        # Process student list Excel file
        if 'student-list-excel' in request.files:
            file = request.files['student-list-excel']
            if file and file.filename.endswith('.xlsx'):
                try:
                    df = pd.read_excel(file)
                    name_column = None
                    for col in df.columns:
                        if 'full name' in col.lower():
                            name_column = col
                            break

                    if name_column:
                        student_names = df[name_column].dropna().tolist()
                        for student_name in student_names:
                            new_student = EvaluationListOfStudentNames(
                                evaluation_list_of_student_names_documentation_id=documentation_id,
                                evaluation_list_of_student_names_student=student_name
                            )
                            db.session.add(new_student)
                except Exception as e:
                    flash(f"Failed to process student list: {str(e)}", "error")

        # Handle photo documentation images upload
        photo_doc_images = request.files.getlist('photo-documentation-images[]')
        for image in photo_doc_images:
            if image and allowed_image_file(image.filename):
                try:
                    # Upload to Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        image,
                        folder="event_photo_documentation_images",
                        resource_type="auto"
                    )

                    # Create database entry for the image
                    new_image = EventPhotoDocumentationImages(
                        event_photo_documentation_images_documentation_id=documentation_id,
                        event_photo_documentation_images_cloudinary_url=upload_result['secure_url'],
                        event_photo_documentation_images_cloudinary_public_id=upload_result['public_id']
                    )
                    db.session.add(new_image)
                except Exception as e:
                    flash(f"Failed to upload event photo documentation image: {str(e)}", "error")

        db.session.commit()
        flash("Documentation added successfully!", "success")
        return redirect(url_for('documentation.documentation_overview'))

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
    activity_reports = db.session.query(ActivityReportForms).join(Events, ActivityReportForms.activity_report_forms_concept_paper_forms_id == Events.events_concept_paper_forms_id).all()

    # Query for learning journal forms and include related events
    learning_journals = db.session.query(LearningJournalForms).join(Events, LearningJournalForms.learning_journal_forms_concept_paper_forms_id == Events.events_concept_paper_forms_id).all()

    return render_template('documentation/add-documentation.html', events=events, academic_years=academic_years, users=users, signatories=signatories, activity_reports=activity_reports, learning_journals=learning_journals)


@documentation_bp.route("/update-documentation-status/<int:documentation_id>", methods=["POST"])
@login_required
def update_documentation_status(documentation_id):
    data = request.get_json()
    new_status = data.get('status')

    # Find the documentation by ID
    documentation = Documentation.query.get_or_404(documentation_id)

    # Update the documentation status
    documentation.documentation_status = new_status
    db.session.commit()

    return jsonify(success=True)


@documentation_bp.route('/update-documentation/<int:documentation_id>', methods=['GET', 'POST'])
@login_required
def update_documentation(documentation_id):
    documentation = Documentation.query.get_or_404(documentation_id)

    # Get or create learning journal
    learning_journal = None
    if documentation.documentation_learning_journal_forms_id:
        learning_journal = LearningJournalForms.query.get(documentation.documentation_learning_journal_forms_id)
    else:
        learning_journal = LearningJournalForms()
        db.session.add(learning_journal)
        documentation.documentation_learning_journal_forms_id = learning_journal.learning_journal_forms_id

    if request.method == 'POST':
        documentation_events_id = request.form.get('documentation-events-id')
        documentation_academic_year = request.form.get('documentation-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        documentation_semester = request.form.get('documentation-semester')
        documentation_status = request.form.get('documentation-status')
        documentation_type = request.form.get('documentation-type')
        documentation_activity_report_forms_id = request.form.get('documentation-activity-report-forms-id')
        documentation_prepared_by = request.form.get('documentation-prepared-by')
        documentation_learning_journal_forms_id = request.form.get('documentation-learning-journal-forms-id')
        documentation_checked_by = request.form.get('documentation-checked-by')
        documentation_noted_by = request.form.get('documentation-noted-by')
        documentation_date_of_submission = request.form.get('documentation-date-of-submission')

        # Use the value from the additional input field if "Other A.Y." is selected
        if documentation_academic_year == "Other":
            documentation_academic_year = other_academic_year

        # Convert date fields to datetime objects
        documentation_date_of_submission = datetime.strptime(documentation_date_of_submission, '%Y-%m-%d')

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

        # Update strengths
        # First, delete existing strengths
        ActivityStrengths.query.filter_by(
            activity_strengths_documentation_id=documentation_id
        ).delete()

        # Add new strengths
        strengths = request.form.getlist('activity-strengths[]')
        for strength in strengths:
            if strength.strip():  # Only add non-empty strengths
                new_strength = ActivityStrengths(
                    activity_strengths_documentation_id=documentation_id,
                    activity_strengths_content=strength.strip()
                )
                db.session.add(new_strength)

        # Update weaknesses
        ActivityWeaknesses.query.filter_by(
            activity_weaknesses_documentation_id=documentation_id
        ).delete()

        weaknesses = request.form.getlist('activity-weaknesses[]')
        for weakness in weaknesses:
            if weakness.strip():
                new_weakness = ActivityWeaknesses(
                    activity_weaknesses_documentation_id=documentation_id,
                    activity_weaknesses_content=weakness.strip()
                )
                db.session.add(new_weakness)

        # Update recommendations
        ActivityRecommendations.query.filter_by(
            activity_recommendations_documentation_id=documentation_id
        ).delete()

        recommendations = request.form.getlist('activity-recommendations[]')
        for recommendation in recommendations:
            if recommendation.strip():
                new_recommendation = ActivityRecommendations(
                    activity_recommendations_documentation_id=documentation_id,
                    activity_recommendations_content=recommendation.strip()
                )
                db.session.add(new_recommendation)

        # Update Learning Journal fields
        learning_journal.learning_journal_forms_name_of_student = request.form.get('student-name')
        learning_journal.learning_journal_forms_course_year_level = request.form.get('course-year-level')
        learning_journal.learning_journal_forms_id_number = request.form.get('id-number')
        learning_journal.learning_journal_forms_overall_reflection = request.form.get('overall-reflection')
        learning_journal.learning_journal_forms_seen_and_read_by = request.form.get('seen-read-by')
        learning_journal.learning_journal_forms_prepared_by = request.form.get('documentation-prepared-by')
        learning_journal.learning_journal_forms_checked_by = request.form.get('documentation-checked-by')

        # Update learnings
        Learnings.query.filter_by(
            learnings_learning_journal_forms_id=learning_journal.learning_journal_forms_id
        ).delete()

        learnings = request.form.getlist('learnings[]')
        for learning in learnings:
            if learning.strip():
                new_learning = Learnings(
                    learnings_learning_journal_forms_id=learning_journal.learning_journal_forms_id,
                    learnings_content=learning.strip()
                )
                db.session.add(new_learning)

        # Update observations
        Observations.query.filter_by(
            observations_learning_journal_forms_id=learning_journal.learning_journal_forms_id
        ).delete()

        observations = request.form.getlist('observations[]')
        for observation in observations:
            if observation.strip():
                new_observation = Observations(
                    observations_learning_journal_forms_id=learning_journal.learning_journal_forms_id,
                    observations_content=observation.strip()
                )
                db.session.add(new_observation)

        # Get the list of images to delete
        deleted_image_ids = request.form.get('deleted_evaluation_images', '').split(',')
        if deleted_image_ids and deleted_image_ids[0]:  # Check if there are any deleted images
            for image_id in deleted_image_ids:
                image = ResultsOfTheEvaluationImages.query.get(int(image_id))
                if image:
                    try:
                        # Delete from Cloudinary
                        if image.results_of_the_evaluation_images_cloudinary_public_id:
                            cloudinary.uploader.destroy(
                                image.results_of_the_evaluation_images_cloudinary_public_id
                            )
                        # Delete from database
                        db.session.delete(image)
                    except Exception as e:
                        flash('Error deleting some evaluation images', 'error')

        # Handle new evaluation image uploads
        evaluation_images = request.files.getlist('evaluation-images[]')
        if evaluation_images:
            for image in evaluation_images:
                if image and allowed_image_file(image.filename):
                    try:
                        # Upload to Cloudinary
                        upload_result = cloudinary.uploader.upload(image)

                        # Create new evaluation image record
                        new_image = ResultsOfTheEvaluationImages(
                            results_of_the_evaluation_images_documentation_id=documentation_id,
                            results_of_the_evaluation_images_cloudinary_url=upload_result['secure_url'],
                            results_of_the_evaluation_images_cloudinary_public_id=upload_result['public_id']
                        )
                        db.session.add(new_image)
                    except Exception as e:
                        flash('Error uploading some evaluation images', 'error')

        # Handle attendance images
        deleted_attendance_image_ids = request.form.get('deleted_attendance_images', '').split(',')
        if deleted_attendance_image_ids and deleted_attendance_image_ids[0]:
            for image_id in deleted_attendance_image_ids:
                image = SummaryOfAttendanceImages.query.get(int(image_id))
                if image:
                    try:
                        if image.summary_of_attendance_images_cloudinary_public_id:
                            cloudinary.uploader.destroy(
                                image.summary_of_attendance_images_cloudinary_public_id,
                                resource_type="image"
                            )
                        db.session.delete(image)
                    except Exception as e:
                        flash('Error deleting some attendance images', 'error')

        attendance_images = request.files.getlist('attendance-images[]')
        if attendance_images:
            for image in attendance_images:
                if image and allowed_image_file(image.filename):
                    try:
                        upload_result = cloudinary.uploader.upload(image)
                        new_image = SummaryOfAttendanceImages(
                            summary_of_attendance_images_documentation_id=documentation_id,
                            summary_of_attendance_images_cloudinary_url=upload_result['secure_url'],
                            summary_of_attendance_images_cloudinary_public_id=upload_result['public_id']
                        )
                        db.session.add(new_image)
                    except Exception as e:
                        flash('Error uploading some attendance images', 'error')

        # Handle photo documentation images
        deleted_photo_doc_image_ids = request.form.get('deleted_photo_doc_images', '').split(',')
        if deleted_photo_doc_image_ids and deleted_photo_doc_image_ids[0]:
            for image_id in deleted_photo_doc_image_ids:
                image = EventPhotoDocumentationImages.query.get(int(image_id))
                if image:
                    try:
                        if image.event_photo_documentation_images_cloudinary_public_id:
                            cloudinary.uploader.destroy(
                                image.event_photo_documentation_images_cloudinary_public_id,
                                resource_type="image"
                            )
                        db.session.delete(image)
                    except Exception as e:
                        flash('Error deleting some photo documentation images', 'error')

        photo_doc_images = request.files.getlist('photo-documentation-images[]')
        if photo_doc_images:
            for image in photo_doc_images:
                if image and allowed_image_file(image.filename):
                    try:
                        upload_result = cloudinary.uploader.upload(image)
                        new_image = EventPhotoDocumentationImages(
                            event_photo_documentation_images_documentation_id=documentation_id,
                            event_photo_documentation_images_cloudinary_url=upload_result['secure_url'],
                            event_photo_documentation_images_cloudinary_public_id=upload_result['public_id']
                        )
                        db.session.add(new_image)
                    except Exception as e:
                        flash('Error uploading some photo documentation images', 'error')

        # Update tally items
        TallyItems.query.filter_by(tally_items_documentation_id=documentation_id).delete()

        tally_items_names = request.form.getlist('tally-items-name[]')
        tally_items_extremely_satisfied = request.form.getlist('tally-items-extremely-satisfied-rating-total[]')
        tally_items_satisfied = request.form.getlist('tally-items-satisfied-rating-total[]')
        tally_items_neutral = request.form.getlist('tally-items-neutral-rating-total[]')
        tally_items_dissatisfied = request.form.getlist('tally-items-dissatisfied-rating-total[]')
        tally_items_extremely_dissatisfied = request.form.getlist('tally-items-extremely-dissatisfied-rating-total[]')

        for i in range(len(tally_items_names)):
            if tally_items_names[i].strip():
                new_tally_item = TallyItems(
                    tally_items_documentation_id=documentation_id,
                    tally_items_name=tally_items_names[i],
                    tally_items_extremely_satisfied_rating_total=int(tally_items_extremely_satisfied[i]),
                    tally_items_satisfied_rating_total=int(tally_items_satisfied[i]),
                    tally_items_neutral_rating_total=int(tally_items_neutral[i]),
                    tally_items_dissatisfied_rating_total=int(tally_items_dissatisfied[i]),
                    tally_items_extremely_dissatisfied_rating_total=int(tally_items_extremely_dissatisfied[i])
                )
                db.session.add(new_tally_item)

        # Update evaluation forms
        EvaluationForm.query.filter_by(evaluation_form_documentation_id=documentation_id).delete()

        evaluation_form_names = request.form.getlist('evaluation-form-name[]')
        evaluation_form_ratings = request.form.getlist('evaluation-form-rating[]')

        for i in range(len(evaluation_form_names)):
            if evaluation_form_names[i].strip():
                rating = evaluation_form_ratings[i] if i < len(evaluation_form_ratings) else None
                new_evaluation_form = EvaluationForm(
                    evaluation_form_documentation_id=documentation_id,
                    evaluation_form_name=evaluation_form_names[i]
                )
                if rating == '5':
                    new_evaluation_form.evaluation_form_extremely_satisfied_rating = 1
                elif rating == '4':
                    new_evaluation_form.evaluation_form_satisfied_rating = 1
                elif rating == '3':
                    new_evaluation_form.evaluation_form_neutral_rating = 1
                elif rating == '2':
                    new_evaluation_form.evaluation_form_dissatisfied_rating = 1
                elif rating == '1':
                    new_evaluation_form.evaluation_form_extremely_dissatisfied_rating = 1
                db.session.add(new_evaluation_form)

        # Update student list
        EvaluationListOfStudentNames.query.filter_by(
            evaluation_list_of_student_names_documentation_id=documentation_id
        ).delete()

        student_names = request.form.getlist('student-names[]')
        for student_name in student_names:
            if student_name.strip():
                new_student = EvaluationListOfStudentNames(
                    evaluation_list_of_student_names_documentation_id=documentation_id,
                    evaluation_list_of_student_names_student=student_name.strip()
                )
                db.session.add(new_student)

        db.session.commit()
        flash('Documentation updated successfully!', 'success')
        return redirect(url_for('documentation.documentation_overview'))

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
    activity_reports = db.session.query(
        ActivityReportForms, ConceptPaperForms.concept_paper_forms_subject
    ).join(
        ConceptPaperForms,
        ActivityReportForms.activity_report_forms_concept_paper_forms_id == ConceptPaperForms.concept_paper_forms_id
    ).all()

    # Prepare activity reports data
    activity_reports_data = [{
        'activity_report_forms_id': report.ActivityReportForms.activity_report_forms_id,
        'events_name': report.concept_paper_forms_subject
    } for report in activity_reports]

    # Query for learning journal forms with concept paper subject
    learning_journals = db.session.query(
        LearningJournalForms, ConceptPaperForms.concept_paper_forms_subject
    ).join(
        ConceptPaperForms,
        LearningJournalForms.learning_journal_forms_concept_paper_forms_id == ConceptPaperForms.concept_paper_forms_id
    ).all()

    # Prepare learning journals data
    learning_journals_data = [{
        'learning_journal_forms_id': journal.LearningJournalForms.learning_journal_forms_id,
        'events_name': journal.concept_paper_forms_subject,
        'learning_journal_forms_name_of_student': journal.LearningJournalForms.learning_journal_forms_name_of_student,
        'learning_journal_forms_course_year_level': journal.LearningJournalForms.learning_journal_forms_course_year_level,
        'learning_journal_forms_id_number': journal.LearningJournalForms.learning_journal_forms_id_number,
        'learning_journal_forms_date': journal.LearningJournalForms.learning_journal_forms_date,
        'learning_journal_forms_overall_reflection': journal.LearningJournalForms.learning_journal_forms_overall_reflection,
        'learning_journal_forms_prepared_by': journal.LearningJournalForms.learning_journal_forms_prepared_by,
        'learning_journal_forms_seen_and_read_by': journal.LearningJournalForms.learning_journal_forms_seen_and_read_by,
        'learning_journal_forms_checked_by': journal.LearningJournalForms.learning_journal_forms_checked_by
    } for journal in learning_journals]

    # Get tally items
    tally_items = TallyItems.query.filter_by(tally_items_documentation_id=documentation_id).all()

    # Get evaluation images
    evaluation_images = ResultsOfTheEvaluationImages.query.filter_by(
        results_of_the_evaluation_images_documentation_id=documentation_id
    ).all()

    # Get attendance images
    attendance_images = SummaryOfAttendanceImages.query.filter_by(
        summary_of_attendance_images_documentation_id=documentation_id
    ).all()

    # Get photo documentation images
    photo_doc_images = EventPhotoDocumentationImages.query.filter_by(
        event_photo_documentation_images_documentation_id=documentation_id
    ).all()

    # Get evaluation forms
    evaluation_forms = EvaluationForm.query.filter_by(
        evaluation_form_documentation_id=documentation_id
    ).all()

    # Get student list
    evaluation_student_list = EvaluationListOfStudentNames.query.filter_by(
        evaluation_list_of_student_names_documentation_id=documentation_id
    ).all()

    # Get learnings and observations
    learnings = []
    observations = []
    if documentation.documentation_learning_journal_forms_id:
        learning_journal = LearningJournalForms.query.get(documentation.documentation_learning_journal_forms_id)
        if learning_journal:
            learnings = Learnings.query.filter_by(
                learnings_learning_journal_forms_id=learning_journal.learning_journal_forms_id
            ).all()
            observations = Observations.query.filter_by(
                observations_learning_journal_forms_id=learning_journal.learning_journal_forms_id
            ).all()

    # Create evaluation forms dictionary
    evaluation_forms_dict = {}
    for form in evaluation_forms:
        evaluation_forms_dict[form.evaluation_form_id] = {
            'name': form.evaluation_form_name,
            'rating': None
        }
        if form.evaluation_form_extremely_satisfied_rating:
            evaluation_forms_dict[form.evaluation_form_id]['rating'] = '5'
        elif form.evaluation_form_satisfied_rating:
            evaluation_forms_dict[form.evaluation_form_id]['rating'] = '4'
        elif form.evaluation_form_neutral_rating:
            evaluation_forms_dict[form.evaluation_form_id]['rating'] = '3'
        elif form.evaluation_form_dissatisfied_rating:
            evaluation_forms_dict[form.evaluation_form_id]['rating'] = '2'
        elif form.evaluation_form_extremely_dissatisfied_rating:
            evaluation_forms_dict[form.evaluation_form_id]['rating'] = '1'

    return render_template('documentation/update-documentation.html',
                         documentation=documentation,
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
                         evaluation_forms=evaluation_forms_dict
    )


@documentation_bp.route('/delete-documentation/<int:documentation_id>', methods=['GET', 'POST'])
@login_required
def delete_documentation(documentation_id):
    documentation = Documentation.query.get_or_404(documentation_id)

    if request.method == 'POST':
        try:
            # Get the documentation and its associated images
            documentation = Documentation.query.get_or_404(documentation_id)
            evaluation_images = ResultsOfTheEvaluationImages.query.filter_by(
                results_of_the_evaluation_images_documentation_id=documentation_id
            ).all()

            # Delete images from Cloudinary and database
            for image in evaluation_images:
                try:
                    # Delete from Cloudinary
                    if image.results_of_the_evaluation_images_cloudinary_public_id:
                        cloudinary.uploader.destroy(
                            image.results_of_the_evaluation_images_cloudinary_public_id,
                            resource_type="image"
                        )
                    # Delete database entry
                    db.session.delete(image)
                except Exception as e:
                    flash('Error deleting some evaluation images', 'error')
                    # Continue with deletion even if one image fails

            # Get and delete attendance images
            attendance_images = SummaryOfAttendanceImages.query.filter_by(
                summary_of_attendance_images_documentation_id=documentation_id
            ).all()

            # Delete attendance images from Cloudinary and database
            for image in attendance_images:
                try:
                    if image.summary_of_attendance_images_cloudinary_public_id:
                        cloudinary.uploader.destroy(
                            image.summary_of_attendance_images_cloudinary_public_id,
                            resource_type="image"
                        )
                    db.session.delete(image)
                except Exception as e:
                    flash('Error deleting some attendance images', 'error')

            # Get and delete event photo documentation images
            event_photos = EventPhotoDocumentationImages.query.filter_by(
                event_photo_documentation_images_documentation_id=documentation_id
            ).all()

            # Delete event photo documentation images from Cloudinary and database
            for image in event_photos:
                try:
                    if image.event_photo_documentation_images_cloudinary_public_id:
                        cloudinary.uploader.destroy(
                            image.event_photo_documentation_images_cloudinary_public_id,
                            resource_type="image"
                        )
                    db.session.delete(image)
                except Exception as e:
                    flash('Error deleting some event photo documentation images', 'error')

            # Delete the documentation entry
            db.session.delete(documentation)
            db.session.commit()

            flash('Documentation deleted successfully!', 'success')
            return redirect(url_for('documentation.documentation_overview'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to delete documentation.', 'error')

    return render_template('documentation/delete-documentation.html', documentation=documentation)


@documentation_bp.route('/get-related-forms/<int:event_id>', methods=['GET'])
@login_required
def get_related_forms(event_id):
    # Query for the concept paper form ID related to the event
    concept_paper_form_id = db.session.query(Events.events_concept_paper_forms_id).filter(Events.events_id == event_id).scalar()

    # Query for activity report forms related to the concept paper form
    activity_reports = db.session.query(ActivityReportForms).filter(ActivityReportForms.activity_report_forms_concept_paper_forms_id == concept_paper_form_id).all()

    # Query for learning journal forms related to the concept paper form
    learning_journals = db.session.query(LearningJournalForms).filter(LearningJournalForms.learning_journal_forms_concept_paper_forms_id == concept_paper_form_id).all()

    # Get unique signatory IDs from learning_journal_forms_checked_by
    checked_by_ids = set()
    for journal in learning_journals:
        if journal.learning_journal_forms_checked_by:
            checked_by_ids.add(journal.learning_journal_forms_checked_by)

    # Query for filtered signatories
    signatories = db.session.query(Signatories).filter(Signatories.signatory_id.in_(checked_by_ids)).all()

    # Prepare the data to be sent as JSON
    activity_reports_data = [{'activity_report_forms_id': report.activity_report_forms_id, 'events_name': report.concept_paper_form.concept_paper_forms_subject} for report in activity_reports]

    learning_journals_data = [{
        'learning_journal_forms_id': journal.learning_journal_forms_id,
        'events_name': journal.concept_paper_form.concept_paper_forms_subject,
        'learning_journal_forms_checked_by': journal.learning_journal_forms_checked_by
    } for journal in learning_journals]

    signatories_data = [{
        'signatory_id': signatory.signatory_id,
        'signatory_first_name': signatory.signatory_first_name,
        'signatory_last_name': signatory.signatory_last_name,
        'signatory_position': signatory.signatory_position,
        'signatory_department': signatory.signatory_department
    } for signatory in signatories]

    return jsonify(activity_reports=activity_reports_data, learning_journals=learning_journals_data, signatories=signatories_data)


@documentation_bp.route('/get-activity-report-details/<int:activity_report_id>', methods=['GET'])
@login_required
def get_activity_report_details(activity_report_id):
    # Query for activity strengths related to the activity report form
    strengths = db.session.query(ActivityStrengths).join(ActivityReportFormsActivityStrengths).filter(ActivityReportFormsActivityStrengths.activity_report_forms_id == activity_report_id).all()

    # Query for activity weaknesses related to the activity report form
    weaknesses = db.session.query(ActivityWeaknesses).join(ActivityReportFormsActivityWeaknesses).filter(ActivityReportFormsActivityWeaknesses.activity_report_forms_id == activity_report_id).all()

    # Query for activity recommendations related to the activity report form
    recommendations = db.session.query(ActivityRecommendations).join(ActivityReportFormsActivityRecommendations).filter(ActivityReportFormsActivityRecommendations.activity_report_forms_id == activity_report_id).all()

    # Prepare the data to be sent as JSON
    strengths_data = [{'activity_strengths_content': strength.activity_strengths_content} for strength in strengths]
    weaknesses_data = [{'activity_weaknesses_content': weakness.activity_weaknesses_content} for weakness in weaknesses]
    recommendations_data = [{'activity_recommendations_content': recommendation.activity_recommendations_content} for recommendation in recommendations]

    return jsonify(strengths=strengths_data, weaknesses=weaknesses_data, recommendations=recommendations_data)


@documentation_bp.route('/process-student-excel', methods=['POST'])
@login_required
def process_student_excel():
    if 'excel_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})

    file = request.files['excel_file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})

    if not file.filename.endswith('.xlsx'):
        return jsonify({'success': False, 'error': 'Please upload an Excel (.xlsx) file'})

    try:
        # Read the Excel file
        df = pd.read_excel(file)

        # Find column containing 'full name' (case insensitive)
        name_column = None
        for col in df.columns:
            if 'full name' in col.lower():
                name_column = col
                break

        if name_column is None:
            return jsonify({'success': False, 'error': 'No column containing "full name" found'})

        # Get student names
        student_names = df[name_column].dropna().tolist()

        return jsonify({
            'success': True,
            'students': student_names
        })

    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to process Excel file'})


@documentation_bp.route('/generate-documentation-pdf/<int:documentation_id>')
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
    
    IMPORTANT: This function requires the following models that are currently
    missing from the models package and need to be created:
    - LearningJournalForms
    - Learnings
    - Observations
    - PersonnelInChargeForms
    - ActivityReportFormsActivityStrengths (association table)
    - ActivityReportFormsActivityWeaknesses (association table)
    - ActivityReportFormsActivityRecommendations (association table)
    
    TODO: To complete this function:
    1. Create the missing models in the models package
    2. Copy the complete implementation from app.py lines 4517-5787
    3. Update all url_for calls to use the blueprint prefix (e.g., url_for('documentation.documentation_overview'))
    4. Replace 'app.logger' with current_app.logger or import current_app
    """
    
    # For now, return an error indicating the function needs to be completed
    return jsonify({
        'success': False,
        'error': 'PDF generation not yet implemented in blueprint. Copy from app.py lines 4517-5787 after creating missing models.'
    }), 501
