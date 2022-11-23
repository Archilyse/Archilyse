from concurrent import futures

import requests

user = "admin"
password = "admin"  # noqa: B105
api_target = "https://slam.archilyse.com/api"

response = requests.post(
    f"{api_target}/auth/login", json={"user": user, "password": password}
)
assert response.ok, response
token = response.json()["access_token"]


def request_clients():
    return requests.get(
        f"{api_target}/client",
        headers={"Authorization": f"Bearer {token}", "Cache-Control": "no-cache"},
        cookies={},
    ).ok


with futures.ThreadPoolExecutor(max_workers=30) as executor:
    executors = [
        executor.submit(
            request_clients,
        )
        for i in range(50)
    ]

for executor in executors:
    # It has no effect but raises exception from the threads if any
    executor.result()
