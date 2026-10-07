from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_get_cart_without_auth():
    response = client.get("/cart")
    assert response.status_code == 401


def test_add_to_cart_without_auth():
    response = client.post(
        "/cart/items",
        json={
            "product_id": 999999,
            "quantity": 1
        }
    )
    assert response.status_code == 401


def test_update_cart_item_without_auth():
    response = client.put(
        "/cart/items/999999",
        json={"quantity": 2}
    )
    assert response.status_code == 401


def test_delete_cart_item_without_auth():
    response = client.delete("/cart/items/999999")
    assert response.status_code == 401


def test_clear_cart_without_auth():
    response = client.delete("/cart")
    assert response.status_code == 401