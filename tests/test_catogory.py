from  fastapi.testclient import TestClient
from  app.main import app
client=TestClient(app)
def test_get_categories_without_auth():
    response = client.get("/categories")
    assert response.status_code == 401


def test_get_category_without_auth():
    response = client.get("/categories/999999")
    assert response.status_code == 401


def test_create_category_without_auth():
    response = client.post(
        "/categories",
        json={"name": "Test Category"}
    )
    assert response.status_code == 401


def test_update_category_without_auth():
    response = client.put(
        "/categories/999999",
        json={"name": "Updated Category"}
    )
    assert response.status_code == 401


def test_delete_category_without_auth():
    response = client.delete("/categories/999999")
    assert response.status_code == 401

