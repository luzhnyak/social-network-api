from fastapi.testclient import TestClient


def test_login(client: TestClient):
    data = {
        "email": "oleg.luzhnyak@gmail.com",
        "password": "oleg123",
    }
    response = client.post("/auth/login/", json=data)
    assert response.status_code == 200


def test_login_not_found(client: TestClient):
    data = {
        "email": "not_user@gmail.com",
        "password": "testpassword2",
    }
    response = client.post("/auth/login/", json=data)
    assert response.status_code == 401
