"""
Configuration classes for E-Council application.
Provides environment-specific configuration management.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings."""
    
    # Flask Core Configuration
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = False
    TESTING = False
    
    # Upload Configuration
    UPLOAD_FOLDER = 'uploads/receipts'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Session Configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Ensure upload folder exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Development-specific overrides
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Production-specific security settings
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_SAMESITE = 'Strict'


class TestingConfig(Config):
    """Testing environment configuration."""
    
    DEBUG = True
    TESTING = True
    
    # Testing-specific overrides
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    SESSION_COOKIE_SECURE = False


class DatabaseConfig:
    """Database configuration settings."""
    
    @staticmethod
    def get_database_uri():
        """Get database URI from environment variables."""
        return os.getenv("SQLALCHEMY_DATABASE_URI")
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = get_database_uri.__func__()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL query logging


class EmailConfig:
    """Email configuration settings."""
    
    # Flask Mail Configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS") == 'True'
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL") == 'True'
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
    
    # Email Settings
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False


class CloudinaryConfig:
    """Cloudinary configuration settings."""
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    CLOUDINARY_SECURE = True
    
    @staticmethod
    def configure():
        """Configure Cloudinary with environment variables."""
        import cloudinary
        cloudinary.config(
            cloud_name=CloudinaryConfig.CLOUDINARY_CLOUD_NAME,
            api_key=CloudinaryConfig.CLOUDINARY_API_KEY,
            api_secret=CloudinaryConfig.CLOUDINARY_API_SECRET,
            secure=CloudinaryConfig.CLOUDINARY_SECURE
        )


class AIConfig:
    """AI configuration settings."""
    
    # Google Gemini AI Configuration
    GOOGLE_GEMINI_AI_API_KEY = os.getenv("GOOGLE_GEMINI_AI_API_KEY")
    GEMINI_MODEL = 'gemini-1.5-flash'
    
    # AI Safety Settings
    AI_SAFETY_SETTINGS = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'
    }
    
    @staticmethod
    def configure():
        """Configure Google Gemini AI with environment variables."""
        import google.generativeai as genai
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        genai.configure(api_key=AIConfig.GOOGLE_GEMINI_AI_API_KEY)
        
        # Convert string safety settings to actual enums
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
        
        return safety_settings


class LoginConfig:
    """Flask-Login configuration settings."""
    
    # Flask-Login Configuration
    LOGIN_VIEW = 'login'
    LOGIN_MESSAGE = "You need to be logged in to access this page."
    LOGIN_MESSAGE_CATEGORY = "error"
    REFRESH_MESSAGE = "Please re-login to access this page."
    REFRESH_MESSAGE_CATEGORY = "info"


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """
    Get configuration class based on environment.
    
    Args:
        env: Environment name (development, production, testing)
              If None, uses FLASK_ENV or defaults to development
        
    Returns:
        Configuration class for the specified environment
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    return config.get(env, DevelopmentConfig)