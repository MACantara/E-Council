from flask import render_template, request, redirect, url_for, flash

from models import Users

def register_routes(app, db):
    """
    Registers all the routes for the application.
    """

    @app.route("/")
    def index():
        """
        Handles the home page.

        Returns:
            str: The rendered home page.
        """
        return render_template("index.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        """
        Handles the signup page.
        """
        if request.method == "GET":
            return render_template("signup.html")
        elif request.method == "POST":
            users_first_name = request.form.get("users_first_name")
            users_last_name = request.form.get("users_last_name")
            users_username = request.form.get("users_username")
            users_email = request.form.get("users_email")
            users_role = request.form.get("users_role")
            users_password = request.form.get("users_password")
            users_email_verified = request.form.get("users_email_verified")

            user = Users(
                users_first_name=users_first_name,
                users_last_name=users_last_name,
                users_username=users_username,
                users_email=users_email,
                users_role=users_role,
                users_email_verified=users_email_verified,
            )

            user.set_password(users_password)

            db.session.add(user)
            db.session.commit()

            flash("User created!", "success")

            users = Users.query.all()
            return redirect(url_for("index"))
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """
        Handles the login page.
        """
        if request.method == "GET":
            return render_template("login.html")
        elif request.method == "POST":
            users_username = request.form.get("users_username")
            users_password = request.form.get("users_password")

            user = Users.query.filter_by(users_username=users_username or users_email).first()

            if user and user.check_password(users_password):
                flash("Login successful!", "success")
                return redirect(url_for("index"))
            else:
                flash("Login failed!", "error")
                return redirect(url_for("login"))

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        """
        Handles the forgot password page.
        """
        return render_template("forgot-password.html")

    @app.route("/reset-password", methods=["GET", "POST"])
    def reset_password():
        """
        Handles the reset password page.
        """
        return render_template("reset-password.html")

    @app.route("/account")
    def account():
        """
        Handles the account page.
        """
        return render_template("account.html")

    @app.route("/account-settings", methods=["GET", "POST"])
    def account_settings():
        """
        Handles the edit account page.
        """
        return render_template("account-settings.html")

    @app.route("/email-settings", methods=["GET", "POST"])
    def email_settings():
        """
        Handles the email settings page.
        """
        return render_template("email-settings.html")

    @app.route("/password-security-settings", methods=["GET", "POST"])
    def password_security_settings():
        """
        Handles the password & security settings page.
        """
        return render_template("password-security-settings.html")

    @app.route("/council-overview")
    def council_overview():
        """
        Handles the council overview page.
        """
        return render_template("council-overview.html")

    @app.route("/events-overview")
    def events_overview():
        """
        Handles the events overview page.
        """
        return render_template("events-overview.html")
    
    @app.route("/add-event")
    def add_event():
        """
        Handles the add event page.
        """
        return render_template("add-event.html")
    
    @app.route("/event-dashboard")
    def event_dashboard():
        """
        Handles the event dashboard page.
        """
        return render_template("event-dashboard.html")
    
    @app.route("/add-transaction")
    def add_transaction():
        """
        Handles the add transaction page.
        """
        return render_template("add-transaction.html")
    
    @app.route("/invite-user")
    def invite_user():
        """
        Handles the invite user page.
        """
        return render_template("invite-user.html")
    
    @app.route("/concept-papers-overview")
    def concept_papers_overview():
        """
        Handles the concept papers overview page.
        """
        return render_template("concept-papers-overview.html")
    
    @app.route("/documentation-overview")
    def documentation_overview():
        """
        Handles the documentation overview page.
        """
        return render_template("documentation-overview.html")
    
    @app.route("/financial-reports-overview")
    def financial_reports_overview():
        """
        Handles the financial reports overview page.
        """
        return render_template("financial-reports-overview.html")
    
    @app.route("/accreditation-requirements-overview")
    def accreditation_requirements_overview():
        """
        Handles the accreditation requirements overview page.
        """
        return render_template("accreditation-requirements-overview.html")
    
    @app.route("/board-resolutions-overview")
    def board_resolutions_overview():
        """
        Handles the board resolutions overview page.
        """
        return render_template("board-resolutions-overview.html")
    
    @app.route("/notable-achievement-reports-overview")
    def notable_achievement_reports_overview():
        """
        Handles the notable achievement reports overview page.
        """
        return render_template("notable-achievement-reports-overview.html")
    
    @app.route("/society-achievement-and-compliances-reports-overview")
    def society_accomplishment_and_compliance_reports_overview():
        """
        Handles the society accomplishment and compliance reports overview page.
        """
        return render_template("society-accomplishment-and-compliance-reports-overview.html")
    
    @app.route("/minutes-of-the-meeting-overview")
    def minutes_of_the_meeting_overview():
        """
        Handles the minutes of the meeting overview page.
        """
        return render_template("minutes-of-the-meeting-overview.html")
    
    @app.route("/student-enrichment-activity-reports-overview")
    def student_enrichment_activity_reports_overview():
        """
        Handles the student enrichment activity reports overview page.
        """
        return render_template("student-enrichment-activity-reports-overview.html")
    
    @app.route("/end-of-semester-reports-overview")
    def end_of_semester_reports_overview():
        """
        Handles the end of semester reports overview page.
        """
        return render_template("end-of-semester-reports-overview.html")
    
    @app.route("/calendar-of-activities-overview")
    def calendar_of_activities_overview():
        """
        Handles the calendar of activities overview page.
        """
        return render_template("calendar-of-activities-overview.html")
    
    @app.route("/semestral-clearance-overview")
    def semestral_clearance_overview():
        """
        Handles the semestral clearance overview page.
        """
        return render_template("semestral-clearance-overview.html")