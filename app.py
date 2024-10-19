import os
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Users(db.Model):
    __tablename__ = "users"

    users_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    users_first_name = db.Column(db.String(50), nullable=False)
    users_last_name = db.Column(db.String(50), nullable=False)
    users_username = db.Column(db.String(50), unique=True, nullable=False)
    users_email = db.Column(db.String(100), nullable=False)
    users_department = db.Column(db.String(100), nullable=False)
    users_role = db.Column(db.String(50), nullable=False)
    users_password = db.Column(db.String(255), nullable=False)
    users_email_verified = db.Column(db.Integer, nullable=False)

    def set_password(self, password):
        self.users_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.users_password, password)

    def __repr__(self):
        return f"Users({self.users_id}, {self.users_first_name}, {self.users_last_name}, {self.users_username}, {self.users_email}, {self.users_department}, {self.users_role}, {self.users_password}, {self.users_email_verified})"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        users_first_name = request.form.get("users-first-name")
        users_last_name = request.form.get("users-last-name")
        users_username = request.form.get("users-username")
        users_email = request.form.get("users-email")
        users_department = request.form.get("users-department")
        users_role = request.form.get("users-role")
        users_password = request.form.get("users-password")
        users_repeat_password = request.form.get("users-repeat-password")
        users_email_verified = 0

        # Validation
        if not users_first_name or not users_last_name or not users_username or not users_email or not users_department or not users_role or not users_password:
            flash("All fields are required.", "error")
            return render_template("signup.html")

        # Check if username already exists
        if Users.query.filter_by(users_username=users_username).first():
            flash("Username already exists.", "error")
            return render_template("signup.html")

        # Check if passwords match
        if users_password != users_repeat_password:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        # Check password requirements
        if len(users_password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("signup.html")
        if not any(char.isupper() for char in users_password):
            flash("Password must contain at least one uppercase letter.", "error")
            return render_template("signup.html")
        if not any(char.islower() for char in users_password):
            flash("Password must contain at least one lowercase letter.", "error")
            return render_template("signup.html")
        if not any(char.isdigit() for char in users_password):
            flash("Password must contain at least one number.", "error")
            return render_template("signup.html")
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in users_password):
            flash("Password must contain at least one special character.", "error")
            return render_template("signup.html")

        user = Users(
            users_first_name=users_first_name,
            users_last_name=users_last_name,
            users_username=users_username,
            users_email=users_email,
            users_department=users_department,
            users_role=users_role,
            users_email_verified=users_email_verified,
        )

        user.set_password(users_password)

        db.session.add(user)
        db.session.commit()

        flash("Account created!", "success")

        return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        users_username = request.form.get("users-username")
        users_password = request.form.get("users-password")

        user = Users.query.filter_by(users_username=users_username).first()

        if user and user.check_password(users_password):
            session['users_id'] = user.users_id
            session['users_first_name'] = user.users_first_name
            session['users_last_name'] = user.users_last_name
            session['users_username'] = user.users_username
            session['users_email'] = user.users_email
            session['users_department'] = user.users_department
            session['users_role'] = user.users_role
            flash("Login successful!", "success")
            return redirect(url_for("council_overview"))
        else:
            flash("Login failed!", "error")
            return redirect(url_for("login"))

# Ensure you have a logout route to clear the session
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    return render_template("forgot-password.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    return render_template("reset-password.html")

@app.route("/account")
def account():
    return render_template("account.html")

@app.route("/account-settings", methods=["GET", "POST"])
def account_settings():
    return render_template("account-settings.html")

@app.route("/email-settings", methods=["GET", "POST"])
def email_settings():
    return render_template("email-settings.html")

@app.route("/password-security-settings", methods=["GET", "POST"])
def password_security_settings():
    return render_template("password-security-settings.html")

@app.route("/council-overview")
def council_overview():
    return render_template("council-overview.html")

@app.route("/events-overview")
def events_overview():
    return render_template("events-overview.html")

@app.route("/event-dashboard")
def event_dashboard():
    return render_template("event-dashboard.html")

@app.route("/add-transaction")
def add_transaction():
    return render_template("add-transaction.html")

@app.route("/invite-user")
def invite_user():
    return render_template("invite-user.html")

@app.route("/event-invite-rejected")
def event_invite_rejected():
    return render_template("event-invite-rejected.html")

@app.route("/event-invite-accepted")
def event_invite_accepted():
    return render_template("event-invite-accepted.html")

@app.route("/concept-papers-overview")
def concept_papers_overview():
    return render_template("concept-papers-overview.html")

@app.route("/documentation-overview")
def documentation_overview():
    return render_template("documentation-overview.html")

@app.route("/financial-reports-overview")
def financial_reports_overview():
    return render_template("financial-reports-overview.html")

@app.route("/accreditation-requirements-overview")
def accreditation_requirements_overview():
    return render_template("accreditation-requirements-overview.html")

@app.route("/board-resolutions-overview")
def board_resolutions_overview():
    return render_template("board-resolutions-overview.html")

@app.route("/notable-achievement-reports-overview")
def notable_achievement_reports_overview():
    return render_template("notable-achievement-reports-overview.html")

@app.route("/society-achievement-and-compliances-reports-overview")
def society_accomplishment_and_compliance_reports_overview():
    return render_template("society-accomplishment-and-compliance-reports-overview.html")

@app.route("/minutes-of-the-meeting-overview")
def minutes_of_the_meeting_overview():
    return render_template("minutes-of-the-meeting-overview.html")

@app.route("/student-enrichment-activity-reports-overview")
def student_enrichment_activity_reports_overview():
    return render_template("student-enrichment-activity-reports-overview.html")

@app.route("/end-of-semester-reports-overview")
def end_of_semester_reports_overview():
    return render_template("end-of-semester-reports-overview.html")

@app.route("/calendar-of-activities-overview")
def calendar_of_activities_overview():
    return render_template("calendar-of-activities-overview.html")

@app.route("/semestral-clearance-overview")
def semestral_clearance_overview():
    return render_template("semestral-clearance-overview.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)