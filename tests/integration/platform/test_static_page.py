from fastapi.testclient import TestClient


def test_root_serves_turkish_page(client: TestClient) -> None:
    """AC-20: title, declared language and UTF-8 Turkish characters."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    html = response.content.decode("utf-8")
    assert '<html lang="tr">' in html
    assert "<title>Polsan İzin Yönetimi</title>" in html
    assert "Kontrol ediliyor…" in html


def test_assets_are_served_with_types_a_browser_will_run(client: TestClient) -> None:
    """With nosniff, a module script served as text/plain would not run at all."""
    script = client.get("/static/app.js")
    assert script.status_code == 200
    assert script.headers["content-type"].startswith("text/javascript")
    stylesheet = client.get("/static/styles.css")
    assert stylesheet.headers["content-type"].startswith("text/css")


def test_unknown_page_returns_problem_json(client: TestClient) -> None:
    """Plan 0001 risk 6: every 404 uses the one problem pattern."""
    for path in ("/does-not-exist", "/static/missing.js"):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json()["code"] == "platform.not_found"
