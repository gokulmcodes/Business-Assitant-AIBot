from app import app


def test_home_page():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "ok"


def test_login_page():
    client = app.test_client()

    response = client.get("/login")

    assert response.status_code == 200


def test_signup_page():
    client = app.test_client()

    response = client.get("/signup")

    assert response.status_code == 200


def test_about_page():
    client = app.test_client()

    response = client.get("/about")

    assert response.status_code == 200


def test_features_page():
    client = app.test_client()

    response = client.get("/features")

    assert response.status_code == 200


def test_contact_page():
    client = app.test_client()

    response = client.get("/contact")

    assert response.status_code == 200