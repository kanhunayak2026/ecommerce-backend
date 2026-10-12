
import os
from locust import HttpUser, task, between


class EcommerceUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        email = os.getenv("TEST_EMAIL")
        password = os.getenv("TEST_PASSWORD")

        if not email or not password:
            raise RuntimeError(
                "Set TEST_EMAIL and TEST_PASSWORD first"
            )

        with self.client.post(
            "/login",
            json={"email": email, "password": password},
            name="POST /login",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    self.token = token
                    response.success()
                else:
                    self.token = None
                    response.failure("Access token missing")
            else:
                self.token = None
                response.failure(
                    f"Login failed: HTTP {response.status_code}"
                )

    @task
    def get_products(self):
        if not getattr(self, "token", None):
            return

        self.client.get(
            "/products",
            headers={
                "Authorization": f"Bearer {self.token}"
            },
            name="GET /products",
        )
