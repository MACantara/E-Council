"""
Documentation and evaluation models for E-Council.
"""

from models.base import db

# Note: These models have complex relationships with other models
# Using string references to avoid circular imports


class Documentation(db.Model):
    __tablename__ = 'documentation'

    documentation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    documentation_events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), nullable=True)
    documentation_academic_year = db.Column(db.String(50), nullable=True)
    documentation_semester = db.Column(db.String(50), nullable=True)
    documentation_status = db.Column(db.String(50), nullable=True)
    documentation_departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), nullable=True)
    documentation_type = db.Column(db.String(50), nullable=True)
    documentation_activity_report_forms_id = db.Column(db.Integer, db.ForeignKey('activity_report_forms.activity_report_forms_id'), nullable=True)
    documentation_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    documentation_learning_journal_forms_id = db.Column(db.Integer, db.ForeignKey('learning_journal_forms.learning_journal_forms_id'), nullable=True)
    documentation_checked_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    documentation_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    documentation_date_of_submission = db.Column(db.DateTime, nullable=True)
    documentation_rating = db.Column(db.Float, nullable=True)
    documentation_comments_suggestions = db.Column(db.Text, nullable=True)

    # Relationships - using string references to avoid circular imports
    events = db.relationship('Events', foreign_keys=[documentation_events_id])
    prepared_by_user = db.relationship('Users', foreign_keys=[documentation_prepared_by])
    checked_by_signatory = db.relationship('Signatories', foreign_keys=[documentation_checked_by])
    noted_by_signatory = db.relationship('Signatories', foreign_keys=[documentation_noted_by])
    department = db.relationship('Departments', foreign_keys=[documentation_departments_id])

    def __repr__(self):
        return f'<Documentation {self.documentation_id}: {self.documentation_type}>'


class TallyItems(db.Model):
    __tablename__ = 'tally_items'

    tally_items_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tally_items_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=True)
    tally_items_name = db.Column(db.String(255), nullable=True)
    tally_items_extremely_satisfied_rating_total = db.Column(db.Integer, nullable=True)
    tally_items_satisfied_rating_total = db.Column(db.Integer, nullable=True)
    tally_items_neutral_rating_total = db.Column(db.Integer, nullable=True)
    tally_items_dissatisfied_rating_total = db.Column(db.Integer, nullable=True)
    tally_items_extremely_dissatisfied_rating_total = db.Column(db.Integer, nullable=True)
    
    documentation = db.relationship('Documentation', backref='tally_items', lazy=True)

    def __repr__(self):
        return f'<TallyItems {self.tally_items_id}>'


class ResultsOfTheEvaluationImages(db.Model):
    __tablename__ = 'results_of_the_evaluation_images'

    results_of_the_evaluation_images_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    results_of_the_evaluation_images_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=True)
    results_of_the_evaluation_images_cloudinary_url = db.Column(db.String(255), nullable=True)
    results_of_the_evaluation_images_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    
    documentation = db.relationship('Documentation', backref='results_of_the_evaluation_images', lazy=True)

    def __repr__(self):
        return f'<ResultsOfTheEvaluationImages {self.results_of_the_evaluation_images_id}>'


class EvaluationForm(db.Model):
    __tablename__ = 'evaluation_form'

    evaluation_form_id = db.Column(db.Integer, primary_key=True)
    evaluation_form_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id', ondelete='CASCADE'))
    evaluation_form_name = db.Column(db.String(255))
    evaluation_form_extremely_satisfied_rating = db.Column(db.Integer, default=0)
    evaluation_form_satisfied_rating = db.Column(db.Integer, default=0)
    evaluation_form_neutral_rating = db.Column(db.Integer, default=0)
    evaluation_form_dissatisfied_rating = db.Column(db.Integer, default=0)
    evaluation_form_extremely_dissatisfied_rating = db.Column(db.Integer, default=0)

    # Relationship
    documentation = db.relationship('Documentation', backref=db.backref('evaluation_forms', lazy=True))

    def to_dict(self):
        return {
            'evaluation_form_id': self.evaluation_form_id,
            'evaluation_form_documentation_id': self.evaluation_form_documentation_id,
            'evaluation_form_name': self.evaluation_form_name,
            'evaluation_form_extremely_satisfied_rating': self.evaluation_form_extremely_satisfied_rating,
            'evaluation_form_satisfied_rating': self.evaluation_form_satisfied_rating,
            'evaluation_form_neutral_rating': self.evaluation_form_neutral_rating,
            'evaluation_form_dissatisfied_rating': self.evaluation_form_dissatisfied_rating,
            'evaluation_form_extremely_dissatisfied_rating': self.evaluation_form_extremely_dissatisfied_rating
        }


class SummaryOfAttendanceImages(db.Model):
    __tablename__ = 'summary_of_attendance_images'

    summary_of_attendance_images_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    summary_of_attendance_images_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=True)
    summary_of_attendance_images_cloudinary_url = db.Column(db.String(255), nullable=True)
    summary_of_attendance_images_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    
    documentation = db.relationship('Documentation', backref='summary_of_attendance_images', lazy=True)

    def __repr__(self):
        return f'<SummaryOfAttendanceImages {self.summary_of_attendance_images_id}>'


class EvaluationListOfStudentNames(db.Model):
    __tablename__ = 'evaluation_list_of_student_names'

    evaluation_list_of_student_names_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    evaluation_list_of_student_names_documentation_id = db.Column(
        db.Integer, 
        db.ForeignKey('documentation.documentation_id', ondelete='CASCADE'),
        nullable=True
    )
    evaluation_list_of_student_names_student = db.Column(db.String(255), nullable=True)
    
    documentation = db.relationship(
        'Documentation',
        backref=db.backref('evaluation_list_of_student_names', passive_deletes=True),
        lazy=True
    )

    def __repr__(self):
        return f'<EvaluationListOfStudentNames {self.evaluation_list_of_student_names_id}>'


class EventPhotoDocumentationImages(db.Model):
    __tablename__ = 'event_photo_documentation_images'

    event_photo_documentation_images_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_photo_documentation_images_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=True)
    event_photo_documentation_images_cloudinary_url = db.Column(db.String(255), nullable=True)
    event_photo_documentation_images_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    
    documentation = db.relationship('Documentation', backref='event_photo_documentation_images', lazy=True)

    def __repr__(self):
        return f'<EventPhotoDocumentationImages {self.event_photo_documentation_images_id}>'


class ActivityStrengths(db.Model):
    __tablename__ = 'activity_strengths'

    activity_strengths_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_strengths_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=False)
    activity_strengths_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityStrengths {self.activity_strengths_id}: {self.activity_strengths_content}>'


class ActivityWeaknesses(db.Model):
    __tablename__ = 'activity_weaknesses'

    activity_weaknesses_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_weaknesses_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=False)
    activity_weaknesses_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityWeaknesses {self.activity_weaknesses_id}: {self.activity_weaknesses_content}>'


class ActivityRecommendations(db.Model):
    __tablename__ = 'activity_recommendations'

    activity_recommendations_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_recommendations_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=False)
    activity_recommendations_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityRecommendations {self.activity_recommendations_id}: {self.activity_recommendations_content}>'