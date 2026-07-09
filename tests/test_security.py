"""Tests for HTTP security headers."""


def test_security_headers_on_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers
    csp = response.headers.get("Content-Security-Policy")
    assert "default-src 'self'" in csp
    assert "https://cdn.jsdelivr.net" in csp
    assert "https://unpkg.com" in csp
    assert "https://fonts.googleapis.com" in csp


def test_security_headers_on_login(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers


def test_hsts_header_in_secure_mode(client):
    client.application.config["SESSION_COOKIE_SECURE"] = True
    response = client.get("/")
    assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"


def test_hsts_header_absent_in_insecure_mode(client):
    response = client.get("/")
    assert "Strict-Transport-Security" not in response.headers
