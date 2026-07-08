"""
Tests for configuration management.
"""

import pytest
import os
from config.config import (
    Config,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    DatabaseConfig,
    EmailConfig,
    CloudinaryConfig,
    AIConfig,
    LoginConfig,
    get_config
)


class TestConfigClasses:
    """Test configuration classes."""
    
    def test_base_config_attributes(self):
        """Test base configuration has required attributes."""
        assert hasattr(Config, 'SECRET_KEY')
        assert hasattr(Config, 'DEBUG')
        assert hasattr(Config, 'TESTING')
        assert hasattr(Config, 'UPLOAD_FOLDER')
    
    def test_development_config(self):
        """Test development configuration."""
        assert DevelopmentConfig.DEBUG == True
        assert DevelopmentConfig.TESTING == False
        assert DevelopmentConfig.SESSION_COOKIE_SECURE == False
    
    def test_production_config(self):
        """Test production configuration."""
        assert ProductionConfig.DEBUG == False
        assert ProductionConfig.TESTING == False
        assert ProductionConfig.SESSION_COOKIE_SECURE == True
        assert ProductionConfig.SESSION_COOKIE_SAMESITE == 'Strict'
    
    def test_testing_config(self):
        """Test testing configuration."""
        assert TestingConfig.DEBUG == True
        assert TestingConfig.TESTING == True
    
    def test_database_config(self):
        """Test database configuration."""
        assert hasattr(DatabaseConfig, 'SQLALCHEMY_DATABASE_URI')
        assert hasattr(DatabaseConfig, 'SQLALCHEMY_TRACK_MODIFICATIONS')
        assert DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS == False
    
    def test_email_config(self):
        """Test email configuration."""
        assert hasattr(EmailConfig, 'MAIL_SERVER')
        assert hasattr(EmailConfig, 'MAIL_PORT')
        assert hasattr(EmailConfig, 'MAIL_USERNAME')
        assert hasattr(EmailConfig, 'MAIL_PASSWORD')
    
    def test_cloudinary_config(self):
        """Test Cloudinary configuration."""
        assert hasattr(CloudinaryConfig, 'CLOUDINARY_CLOUD_NAME')
        assert hasattr(CloudinaryConfig, 'CLOUDINARY_API_KEY')
        assert hasattr(CloudinaryConfig, 'CLOUDINARY_API_SECRET')
        assert CloudinaryConfig.CLOUDINARY_SECURE == True
    
    def test_ai_config(self):
        """Test AI configuration."""
        assert hasattr(AIConfig, 'GOOGLE_GEMINI_AI_API_KEY')
        assert hasattr(AIConfig, 'GEMINI_MODEL')
        assert AIConfig.GEMINI_MODEL == 'gemini-1.5-flash'
    
    def test_login_config(self):
        """Test login configuration."""
        assert hasattr(LoginConfig, 'LOGIN_VIEW')
        assert LoginConfig.LOGIN_VIEW == 'login'
        assert hasattr(LoginConfig, 'LOGIN_MESSAGE')


class TestConfigFunctions:
    """Test configuration functions."""
    
    def test_get_config_development(self):
        """Test getting development configuration."""
        config = get_config('development')
        assert config == DevelopmentConfig
    
    def test_get_config_production(self):
        """Test getting production configuration."""
        config = get_config('production')
        assert config == ProductionConfig
    
    def test_get_config_testing(self):
        """Test getting testing configuration."""
        config = get_config('testing')
        assert config == TestingConfig
    
    def test_get_config_default(self):
        """Test getting default configuration."""
        config = get_config()
        assert config == DevelopmentConfig
    
    def test_get_config_invalid(self):
        """Test getting configuration with invalid name."""
        config = get_config('invalid')
        assert config == DevelopmentConfig  # Falls back to default


class TestConfigIntegration:
    """Test configuration integration with environment variables."""
    
    def test_secret_key_from_env(self):
        """Test SECRET_KEY loaded from environment."""
        # This test assumes .env file is loaded
        assert Config.SECRET_KEY is not None
        assert len(Config.SECRET_KEY) > 0
    
    def test_database_uri_from_env(self):
        """Test database URI loaded from environment."""
        assert DatabaseConfig.SQLALCHEMY_DATABASE_URI is not None
        assert 'mysql://' in DatabaseConfig.SQLALCHEMY_DATABASE_URI or 'sqlite://' in DatabaseConfig.SQLALCHEMY_DATABASE_URI