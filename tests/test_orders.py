from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
def test_create_order_without_auth():
    response = client.post("/orders")
    assert response.status_code == 401


def test_get_orders_without_auth():
    response = client.get("/orders")
    assert response.status_code == 401


def test_get_order_without_auth():
    response = client.get("/orders/999999")
    assert response.status_code == 401


def test_cancel_order_without_auth():
    response = client.put("/orders/999999/cancel")
    assert response.status_code == 401

