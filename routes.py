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