"""FastAPI prototype settings for E-Council."""

import os

from config import DatabaseConfig, get_config

FLASK_ENV = os.getenv("FLASK_ENV", "development")
_flask_config = get_config(FLASK_ENV)

SECRET_KEY = _flask_config.SECRET_KEY or os.getenv("SECRET_KEY", "dev-secret-key")
DATABASE_URL = os.getenv("FASTAPI_DATABASE_URI", DatabaseConfig.get_database_uri()) or "sqlite:///./fastapi.db"

# SQLAlchemy defaults to the mysqlclient (MySQLdb) driver for mysql:// URLs, but
# this project uses PyMySQL. If a plain mysql:// URL is provided, rewrite it.
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = "mysql+pymysql://" + DATABASE_URL[len("mysql://"):]

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
