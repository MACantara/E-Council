import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    """
    Create and configure the Flask application.

    Returns:
        flask.app.Flask: The created Flask application.
    """
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

    # Initialize the SQLAlchemy extension.
    db.init_app(app)
    # Initialize the Bcrypt extension.
    bcrypt.init_app(app)

    # Register the routes.
    from routes import register_routes
    register_routes(app, db)

    # Initialize the Migrate extension.
    migrate = Migrate(app, db)

    return app