import sqlite3

import pytest

from app import create_app


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def client(db_path):
    app = create_app(str(db_path))
    app.config["TESTING"] = True
    app.config["ADMIN_PASSWORD"] = "s3cret"
    return app.test_client()


def rows(db_path):
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT name, email, major FROM signups").fetchall()


def test_form_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b'name="email"' in resp.data


def test_valid_signup_saves_and_redirects(client, db_path):
    resp = client.post(
        "/", data={"name": "Ada", "email": "ada@example.com", "major": "ISDS"}
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/thanks")
    assert rows(db_path) == [("Ada", "ada@example.com", "ISDS")]


def test_thanks_page(client):
    resp = client.get("/thanks")
    assert resp.status_code == 200
    assert b"Thank you" in resp.data


@pytest.mark.parametrize(
    "data",
    [
        {"name": "", "email": "ada@example.com", "major": "ISDS"},
        {"name": "Ada", "email": "not-an-email", "major": "ISDS"},
        {"name": "Ada", "email": "ada@example.com", "major": "   "},
    ],
)
def test_invalid_signup_rejected(client, db_path, data):
    resp = client.post("/", data=data)
    assert resp.status_code == 400
    assert rows(db_path) == []


def test_sql_injection_is_stored_literally(client, db_path):
    name = "Robert'); DROP TABLE signups;--"
    client.post("/", data={"name": name, "email": "b@example.com", "major": "CS"})
    assert rows(db_path) == [(name, "b@example.com", "CS")]


def test_admin_requires_password(client):
    resp = client.get("/admin")
    assert resp.status_code == 401
    assert "Basic" in resp.headers["WWW-Authenticate"]


def test_admin_rejects_wrong_password(client):
    resp = client.get("/admin", auth=("admin", "wrong"))
    assert resp.status_code == 401


def test_admin_lists_signups(client):
    client.post("/", data={"name": "Ada", "email": "ada@example.com", "major": "ISDS"})
    client.post("/", data={"name": "Bob", "email": "bob@example.com", "major": "CS"})
    resp = client.get("/admin", auth=("admin", "s3cret"))
    assert resp.status_code == 200
    for text in (b"Ada", b"ada@example.com", b"ISDS", b"Bob", b"bob@example.com", b"CS"):
        assert text in resp.data


def test_admin_escapes_html(client):
    client.post("/", data={"name": "<script>x</script>", "email": "e@x.com", "major": "M"})
    resp = client.get("/admin", auth=("admin", "s3cret"))
    assert b"<script>x</script>" not in resp.data
    assert b"&lt;script&gt;" in resp.data


def test_admin_locked_when_password_not_configured(db_path):
    app = create_app(str(db_path))
    app.config["ADMIN_PASSWORD"] = None
    resp = app.test_client().get("/admin", auth=("admin", ""))
    assert resp.status_code == 401


@pytest.mark.parametrize("path", ["/", "/thanks", "/admin"])
def test_pages_are_responsive_with_bootstrap(client, path):
    resp = client.get(path, auth=("admin", "s3cret"))
    assert resp.status_code == 200
    assert b'name="viewport"' in resp.data
    assert b"bootstrap@5.3.3/dist/css/bootstrap.min.css" in resp.data
    assert b'integrity="sha384-' in resp.data
    assert b"<script" not in resp.data


def test_admin_password_read_from_environment(db_path, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "from-env")
    app = create_app(str(db_path))
    resp = app.test_client().get("/admin", auth=("admin", "from-env"))
    assert resp.status_code == 200
