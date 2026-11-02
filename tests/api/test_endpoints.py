import pytest
from app.utilities.security import encrypt_password



# Health check


def test_health_endpoint(client):
    """GET /health returns 200 and {"ok": true}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}



# Public pages (no auth required)


def test_landing_page_loads(client):
    """GET / returns 200 and HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_browse_publications_loads(client):
    """GET /publications returns 200."""
    response = client.get("/publications")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_browse_with_search_query(client):
    """GET /publications?query=x doesn't crash."""
    response = client.get("/publications?query=nonexistent")
    assert response.status_code == 200


def test_browse_with_year_filter(client):
    """GET /publications?year=2024 doesn't crash."""
    response = client.get("/publications?year=2024")
    assert response.status_code == 200


def test_browse_with_empty_year_is_handled(client):
    """GET /publications?year= (empty) doesn't 500."""
    response = client.get("/publications?year=")
    assert response.status_code == 200


def test_author_graph_loads(client):
    """GET /authors/graph returns 200."""
    response = client.get("/authors/graph")
    assert response.status_code == 200


def test_author_graph_with_search(client):
    """GET /authors/graph?author_query=x doesn't crash."""
    response = client.get("/authors/graph?author_query=test")
    assert response.status_code == 200


def test_author_graph_with_empty_publication_id(client):
    """GET /authors/graph?publication_id= (empty) doesn't 500."""
    response = client.get("/authors/graph?publication_id=")
    assert response.status_code == 200



# Authentication


def test_login_page_loads(client):
    """GET /login returns 200."""
    response = client.get("/login")
    assert response.status_code == 200


def test_register_page_loads(client):
    """GET /register returns 200."""
    response = client.get("/register")
    assert response.status_code == 200


def test_protected_route_shows_401_page_when_logged_out(client):
    """GET /manage/publications without auth shows the 401 page."""
    response = client.get("/manage/publications", follow_redirects=False)
    
    assert response.status_code == 200
    
    body = response.text.lower()
    assert any(
        marker in body
        for marker in ["401", "unauthorized", "session expired", "sign in", "login"]
    )


def test_login_with_invalid_credentials(client):
    """POST /login with wrong credentials fails gracefully."""
    response = client.post(
        "/login",
        data={"username": "ghost", "password": "wrong"},
        follow_redirects=False,
    )
    # redirects back to login with flash message
    assert response.status_code in (200, 303, 307)



# Publicagtion detail 404


def test_publication_detail_not_found(client):
    """GET /publications/999999 returns 404."""
    response = client.get("/publications/999999")
    assert response.status_code == 404