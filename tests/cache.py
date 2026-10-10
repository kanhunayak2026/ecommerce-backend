import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
import time

from fastapi.testclient import TestClient
from app.main import app
from app.redis_client import redis_client

client = TestClient(app)

email = os.getenv("TEST_EMAIL")
password = os.getenv("TEST_PASSWORD")

# Login
login = client.post(
    "/login",
    json={
        "email": email,
        "password": password
    }
)

assert login.status_code == 200, login.text

token = login.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

# Exact Redis key used by /products
cache_key = (
    "products:search=None:"
    "category=None:"
    "min=None:"
    "max=None:"
    "sort=None:"
    "order=asc:"
    "page=1:"
    "limit=10"
)

# Make sure first request is a cache MISS
redis_client.delete(cache_key)

# -------------------------
# First request - MySQL
# -------------------------
start = time.perf_counter()

response1 = client.get(
    "/products?page=1&limit=10",
    headers=headers
)

mysql_time = (time.perf_counter() - start) * 1000

assert response1.status_code == 200, response1.text


# -------------------------
# Second request - Redis
# -------------------------
start = time.perf_counter()

response2 = client.get(
    "/products?page=1&limit=10",
    headers=headers
)

redis_time = (time.perf_counter() - start) * 1000

assert response2.status_code == 200, response2.text


print("\n========== CACHE BENCHMARK ==========")
print(f"First request  : {mysql_time:.2f} ms")
print(f"Second request : {redis_time:.2f} ms")

if redis_time > 0:
    speedup = mysql_time / redis_time
    reduction = (1 - redis_time / mysql_time) * 100

    print(f"Speedup        : {speedup:.2f}x")
    print(f"Time reduction : {reduction:.2f}%")

print("======================================")