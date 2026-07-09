"""
Cloudinary upload tests for the E-Council application.

These tests mock ``cloudinary.uploader.upload`` and exercise the account
routes that upload profile pictures and signatures.
"""

import os
import sys

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
from unittest.mock import MagicMock

import cloudinary
import cloudinary.uploader
import pytest


@pytest.fixture
def mock_cloudinary_upload(monkeypatch):
    """Mock Cloudinary uploader so uploads do not hit the network."""
    fake_result = {
        "secure_url": "https://res.cloudinary.com/test/image.png",
        "public_id": "test_public_id",
    }
    mock_upload = MagicMock(return_value=fake_result)
    monkeypatch.setattr(cloudinary.uploader, "upload", mock_upload)
    monkeypatch.setattr(cloudinary.uploader, "destroy", MagicMock())
    return mock_upload


def _create_image_file(name="test.png", mimetype="image/png"):
    """Create a small in-memory image-like file for testing uploads."""
    return (io.BytesIO(b"fake image bytes"), name)


def test_upload_profile_picture(auth_client, sample_user, mock_cloudinary_upload):
    data = {"profile-picture": _create_image_file("profile.png", "image/png")}
    response = auth_client.post("/account/upload-profile-picture", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    mock_cloudinary_upload.assert_called_once()


def test_upload_profile_picture_invalid_type(auth_client, sample_user, mock_cloudinary_upload):
    data = {"profile-picture": (io.BytesIO(b"text"), "profile.txt", "text/plain")}
    response = auth_client.post("/account/upload-profile-picture", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    mock_cloudinary_upload.assert_not_called()


def test_account_settings_signature_upload(auth_client, sample_user, mock_cloudinary_upload):
    """Posting account settings with a signature file triggers a Cloudinary upload."""
    data = {
        "users-first-name": sample_user.users_first_name,
        "users-last-name": sample_user.users_last_name,
        "users-username": sample_user.users_username,
        "users-department": str(sample_user.users_departments_id),
        "users-role": sample_user.users_role,
        "users-current-password": "Password123!",
        "users-signature": _create_image_file("signature.png", "image/png"),
    }
    response = auth_client.post("/account/account-settings", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    mock_cloudinary_upload.assert_called_once()
