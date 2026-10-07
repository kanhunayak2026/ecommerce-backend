from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_products():
    response = client.get("/products")

    assert response.status_code == 401

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_create_product_without_auth():
    response = client.post(
        "/products",
        json={
            "name": "Test Laptop",
            "price": 50000,
            "category_id": 1
        }
    )

    assert response.status_code == 401

def test_get_product_without_auth():
    response = client.get("/products/999999")

    assert response.status_code == 401

def test_create_product_invalid_data():
    response = client.post(
        "/products",
        json={
            "name": "",
            "price": -100,
            "stock": 0,
            "category_id": 1
        }
    )

    assert response.status_code == 401

def test_update_product_without_auth():
    response = client.put(
        "/products/999999",
        json={
            "name": "Updated Laptop",
            "description": "Updated",
            "price": 60000,
            "stock": 10,
            "category_id": 1
        }
    )
    assert response.status_code == 401

def test_deleted_product_withou_auth():
    response=client.delete("/products/9999")
    assert response.status_code==401


def test_admin_access_with_normal_user():
    login_response = client.post(
        "/login",
        json={
            "email": "string",
            "password": "string"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/admin",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403

def test_get_nonexistent_product():
    login_response = client.post(
        "/login",
        json={
            "email": "string",
            "password": "string"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/products/999999999",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"