from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
def test_login_invalid_data():
    response = client.post(
        "/login",
        json={
            "email": "test@example.com"
        }
    )

    assert response.status_code == 422

def test_login_success():
    response = client.post(
        "/login",
        json={
            "email": "nayakkkanhu640@gmail.com",
            "password": "Kanhu@2004"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"