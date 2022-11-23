import os
from http import HTTPStatus

from locust import HttpUser, between, task

from common_utils.constants import TASK_TYPE
from handlers.db import UnitDBHandler

TIME_LIMIT_IN_S = 1.0


def check_response(response):
    if response.status_code != HTTPStatus.OK:
        response.failure(f"Got wrong response: {response}")
    elif response.elapsed.total_seconds() > TIME_LIMIT_IN_S:
        response.failure("Request took too long")


class MyUser(HttpUser):
    @task
    def get_layout_for_heatmap(self):
        with self.client.get(
            url=f"/api/unit/{self.unit_id}/brooks/simple",
            catch_response=True,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Cache-Control": "no-cache",
            },
            cookies={},
        ) as response:
            check_response(response=response)

    @task
    def get_payload_heatmap(self):
        with self.client.get(
            url=f"/api/unit/{self.unit_id}/simulation_results",
            params={"georeferenced": True, "simulation_type": TASK_TYPE.VIEW_SUN.name},
            catch_response=True,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Cache-Control": "no-cache",
            },
            cookies={},
        ) as response:
            check_response(response=response)

    def on_start(self):
        with self.client.post(
            url="/api/auth/login",
            json={
                "user": os.environ.get("user", "admin"),
                "password": os.environ.get("password", "admin"),
            },
            catch_response=True,
        ) as response:
            assert response.ok, response
            self.token = response.json()["access_token"]
            unit = next(UnitDBHandler.find_iter())
            self.unit_id = unit["id"]

    wait_time = between(0.5, 1.0)
