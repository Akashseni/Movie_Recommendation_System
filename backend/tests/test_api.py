from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_movies():
    resp = client.get("/movies")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) > 0


def test_search_movies():
    resp = client.get("/movies/search", params={"q": "dark knight"})
    assert resp.status_code == 200
    assert any(m["title"] == "The Dark Knight" for m in resp.json())


def test_recommend_success():
    resp = client.get("/recommend", params={"title": "The Godfather", "top_n": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    assert all("similarity" in m for m in body)


def test_recommend_not_found():
    resp = client.get("/recommend", params={"title": "Nonexistent Movie 9999"})
    assert resp.status_code == 404


def test_recommend_by_genre():
    resp = client.get("/recommend/genre", params={"genre": "Horror", "top_n": 2})
    assert resp.status_code == 200
    assert len(resp.json()) <= 2
