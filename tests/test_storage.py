"""Storage abstraction tests for the E-Council application.

These tests verify the storage backend protocol, the factory function, and the
in-memory and local filesystem backends without network calls.
"""

import io

import pytest

from services.storage import (
    CloudinaryStorage,
    LocalFilesystemStorage,
    MemoryStorage,
    NullStorage,
    StorageBackend,
    StorageError,
    get_storage,
)


def test_memory_storage_upload_delete_and_get_url():
    """MemoryStorage should retain files and return memory:// URLs."""
    storage = MemoryStorage()
    file = io.BytesIO(b"fake image bytes")
    file.filename = "test.png"

    result = storage.upload(file)

    assert result["url"].startswith("memory://")
    assert result["public_id"]
    assert storage.get_url(result["public_id"]) == result["url"]
    assert storage.delete(result["public_id"]) is True
    assert storage.get_url(result["public_id"]) is None


def test_memory_storage_delete_returns_false_for_missing_id():
    """Deleting a non-existent public_id from MemoryStorage should return False."""
    storage = MemoryStorage()
    assert storage.delete("missing-id") is False


def test_local_filesystem_storage_upload_and_delete(tmp_path):
    """LocalFilesystemStorage should write files to disk and delete them."""
    upload_dir = tmp_path / "uploads"
    base_url = "/static/uploads"
    storage = LocalFilesystemStorage(upload_dir=upload_dir, base_url=base_url)
    file = io.BytesIO(b"fake image bytes")
    file.filename = "test.png"

    result = storage.upload(file, folder="receipts")

    assert result["url"].startswith(f"{base_url}/receipts/")
    assert result["public_id"].startswith("receipts/")
    assert (upload_dir / result["public_id"]).exists()
    assert storage.get_url(result["public_id"]) == result["url"]

    assert storage.delete(result["public_id"]) is True
    assert not (upload_dir / result["public_id"]).exists()
    assert storage.get_url(result["public_id"]) is None


def test_local_filesystem_storage_unique_filenames(tmp_path):
    """LocalFilesystemStorage should generate unique filenames for each upload."""
    storage = LocalFilesystemStorage(upload_dir=tmp_path, base_url="/static/uploads")
    file1 = io.BytesIO(b"content 1")
    file1.filename = "same.png"
    file2 = io.BytesIO(b"content 2")
    file2.filename = "same.png"

    result1 = storage.upload(file1)
    result2 = storage.upload(file2)

    assert result1["public_id"] != result2["public_id"]
    assert (tmp_path / result1["public_id"]).read_bytes() == b"content 1"
    assert (tmp_path / result2["public_id"]).read_bytes() == b"content 2"


def test_null_storage_is_no_op():
    """NullStorage should not store any data and always return empty values."""
    storage = NullStorage()
    file = io.BytesIO(b"fake image bytes")

    result = storage.upload(file)
    assert result == {"url": "", "public_id": ""}
    assert storage.delete("any-id") is True
    assert storage.get_url("any-id") == ""


def test_get_storage_respects_app_config(app, tmp_path):
    """get_storage should return the backend configured in the app."""
    app.config["STORAGE_PROVIDER"] = "memory"
    storage = get_storage(app)
    assert isinstance(storage, MemoryStorage)

    app.config["STORAGE_PROVIDER"] = "local"
    app.config["STORAGE_LOCAL_PATH"] = str(tmp_path / "uploads")
    app.config["STORAGE_LOCAL_BASE_URL"] = "/static/uploads"
    storage = get_storage(app)
    assert isinstance(storage, LocalFilesystemStorage)
    assert storage.upload_dir == tmp_path / "uploads"


def test_get_storage_unknown_provider_raises(app):
    """get_storage should raise StorageError for an unknown provider."""
    app.config["STORAGE_PROVIDER"] = "unknown"
    with pytest.raises(StorageError):
        get_storage(app)


def test_cloudinary_storage_is_a_storage_backend():
    """CloudinaryStorage should conform to the StorageBackend protocol."""
    assert isinstance(CloudinaryStorage(), StorageBackend)
