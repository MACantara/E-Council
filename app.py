import os
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS") == 'True'
app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL") == 'True'
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

s = URLSafeTimedSerializer(app.config["SECRET_KEY"])

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    flash("You need to be logged in to access this page.", "error")
    return redirect(url_for("login"))

class Users(db.Model, UserMixin):
    __tablename__ = "users"

    users_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    users_first_name = db.Column(db.String(50), nullable=False)
    users_last_name = db.Column(db.String(50), nullable=False)
    users_username = db.Column(db.String(50), unique=True, nullable=False)
    users_email = db.Column(db.String(100), unique=True, nullable=False)
    users_department = db.Column(db.String(100), nullable=False)
    users_role = db.Column(db.String(50), nullable=False)
    users_student_organization = db.Column(db.String(100), nullable=False)
    users_student_organization_position = db.Column(db.String(100), nullable=False)
    users_password = db.Column(db.String(255), nullable=False)
    users_email_verified = db.Column(db.Integer, nullable=False)

    def set_password(self, password):
        self.users_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.users_password, password)

    def get_id(self):
        return str(self.users_id)

    def __repr__(self):
        return f"Users({self.users_id}, {self.users_first_name}, {self.users_last_name}, {self.users_username}, {self.users_email}, {self.users_department}, {self.users_role}, {self.users_student_organization}, {self.users_student_organization_position}, {self.users_password}, {self.users_email_verified})"

def send_verification_email(user_email):
    token = s.dumps(user_email, salt='email-confirm')
    link = url_for('confirm_email', token=token, _external=True)
    msg = Message('New Account Email Verification', recipients=[user_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Welcome to E-Council!</h1>
        <p>You have successfully created an account. Please click the button below to verify your email:</p>
        <a href="{link}" style="background-color: #00578a; color: #ffffff; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px;">Verify Email</a>
        <p style="font-size: 0.8em; color: gray;">Or copy and paste this link into your browser: <br><a href="{link}" style="color: #00578a;">{link}</a></p>
        <p>If you didn't create this account, you can safely ignore this email.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    Welcome to our website!

    You have successfully created an account. Please click the link below to verify your email:
    {link}

    Or copy and paste this link into your browser:
    {link}

    If you didn't create this account, you can safely ignore this email.

    Sincerely,
    E-Council Team
    """
    
    mail.send(msg)
    
@app.route("/send_verification_email/<email>")
def send_verification_email_route(email):
    user = Users.query.filter_by(users_email=email).first_or_404()
    if user.users_email_verified == 0:
        send_verification_email(user.users_email)
        flash(f"A verification email has been sent to your email.", "success")
    else:
        flash("This email is already verified.", "info")
    return redirect(url_for("login"))

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
        
        users_student_organization = request.form.get("users-student-organization") if request.form.get("users-student-organization") else ""
        users_student_organization_position = request.form.get("users-student-organization-position") if request.form.get("users-student-organization-position") else ""

        # Validation
        if not users_first_name or not users_last_name or not users_username or not users_email or not users_department or not users_role or not users_password:
            flash("All fields are required.", "error")
            return render_template("signup.html")

        if users_role == "Student Council Officer":
            if not users_student_organization or not users_student_organization_position:
                flash("Student Organization and Position are required for Student Council Officers.", "error")
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
            users_student_organization=users_student_organization,
            users_student_organization_position=users_student_organization_position,
            users_email_verified=users_email_verified,
        )

        user.set_password(users_password)

        db.session.add(user)
        db.session.commit()
        
        send_verification_email(users_email)

        flash("Account created! Please check your email to verify your account.", "success")

        return redirect(url_for("login"))

@app.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash("The confirmation link has expired.", "error")
        return redirect(url_for("signup"))
    except BadSignature:
        flash("The confirmation link is invalid.", "error")
        return redirect(url_for("signup"))

    user = Users.query.filter_by(users_email=email).first_or_404()
    if user.users_email_verified:
        flash("Account already verified. Please log in.", "info")
    else:
        user.users_email_verified = 1
        db.session.commit()
        flash("Your account has been verified. Please log in.", "success")

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        users_username_email = request.form.get("users-username-email")
        users_password = request.form.get("users-password")

        # Check if the identifier is an email or username
        user = Users.query.filter(
            (Users.users_username == users_username_email) | (Users.users_email == users_username_email)
        ).first()

        if user:
            if user.users_email_verified == 0:
                # Generate verification link
                verification_link = url_for('send_verification_email_route', email=user.users_email, _external=True)
                
                flash(Markup(f"Please verify your email before logging in. <a href='{verification_link}'>Click here to resend the verification email.</a>"), "error")
                return redirect(url_for("login"))

            if user.check_password(users_password):
                login_user(user)
                return redirect(url_for("council_overview"))

        flash("Invalid username/email or password.", "error")
        return redirect(url_for("login"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    return render_template("forgot-password.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    return render_template("reset-password.html")

@app.route("/account")
@login_required
def account():
    return render_template("account.html")

@app.route("/account-settings", methods=["GET", "POST"])
@login_required
def account_settings():
    return render_template("account-settings.html")

@app.route("/email-settings", methods=["GET", "POST"])
@login_required
def email_settings():
    return render_template("email-settings.html")

@app.route("/password-security-settings", methods=["GET", "POST"])
@login_required
def password_security_settings():
    return render_template("password-security-settings.html")

@app.route("/council-overview")
@login_required
def council_overview():
    return render_template("council-overview.html")

@app.route("/events-overview")
@login_required
def events_overview():
    return render_template("events-overview.html")

@app.route("/event-dashboard")
@login_required
def event_dashboard():
    return render_template("event-dashboard.html")

@app.route("/add-transaction")
@login_required
def add_transaction():
    return render_template("add-transaction.html")

@app.route("/invite-user")
@login_required
def invite_user():
    return render_template("invite-user.html")

@app.route("/event-invite-rejected")
@login_required
def event_invite_rejected():
    return render_template("event-invite-rejected.html")

@app.route("/event-invite-accepted")
@login_required
def event_invite_accepted():
    return render_template("event-invite-accepted.html")

@app.route("/concept-papers-overview")
@login_required
def concept_papers_overview():
    return render_template("concept-papers-overview.html")

@app.route("/documentation-overview")
@login_required
def documentation_overview():
    return render_template("documentation-overview.html")

@app.route("/financial-reports-overview")
@login_required
def financial_reports_overview():
    return render_template("financial-reports-overview.html")

@app.route("/accreditation-requirements-overview")
@login_required
def accreditation_requirements_overview():
    return render_template("accreditation-requirements-overview.html")

@app.route("/board-resolutions-overview")
@login_required
def board_resolutions_overview():
    return render_template("board-resolutions-overview.html")

@app.route("/notable-achievement-reports-overview")
@login_required
def notable_achievement_reports_overview():
    return render_template("notable-achievement-reports-overview.html")

@app.route("/society-achievement-and-compliance-reports-overview")
@login_required
def society_accomplishment_and_compliance_reports_overview():
    return render_template("society-accomplishment-and-compliance-reports-overview.html")

@app.route("/minutes-of-the-meeting-overview")
@login_required
def minutes_of_the_meeting_overview():
    return render_template("minutes-of-the-meeting-overview.html")

@app.route("/student-enrichment-activity-reports-overview")
@login_required
def student_enrichment_activity_reports_overview():
    return render_template("student-enrichment-activity-reports-overview.html")

@app.route("/end-of-semester-reports-overview")
@login_required
def end_of_semester_reports_overview():
    return render_template("end-of-semester-reports-overview.html")

@app.route("/calendar-of-activities-overview")
@login_required
def calendar_of_activities_overview():
    return render_template("calendar-of-activities-overview.html")

@app.route("/semestral-clearance-overview")
@login_required
def semestral_clearance_overview():
    return render_template("semestral-clearance-overview.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)