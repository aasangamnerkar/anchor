import os
import uuid
import httpx
from typing import Optional, Dict, Any, Tuple

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")

def _u(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"

def assert_status(resp: httpx.Response, expected: int, msg: str = ""):
    if resp.status_code != expected:
        raise AssertionError(f"{msg}\nExpected {expected}, got {resp.status_code}\nBody: {resp.text}")

def is_json(resp):
    return resp.headers.get("content-type", "").lower().startswith("application/json")

def j(resp):
    return resp.json() if is_json(resp) else None

def server_is_up(client):
    for path in ("/openapi.json", "/docs", "/"):
        try:
            r = client.get(f"{BASE_URL}{path}")
            if r.status_code in (200, 302):
                return True
        except:
            pass
    return False

def api_register(client, email, password, name=None):
    r = client.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    return r, j(r)

def api_login(client, email, password):
    r = client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
    )
    return r, j(r)

def api_logout(client):
    return client.post(f"{BASE_URL}/api/auth/logout")


def test_auth_register_login_logout(client):
    email = f"{_u('user')}@example.com"
    password = "Password123!"

    r, data = api_register(client, email, password, "Test User")
    assert_status(r, 201)
    assert "access_token" in data

    r2, _ = api_register(client, email, password, "Test User")
    assert_status(r2, 409)

    r3, data3 = api_login(client, email, password)
    assert_status(r3, 200)
    assert data3["access_token"]

    r4, _ = api_login(client, email, "wrongpass")
    assert_status(r4, 401)

    r5 = api_logout(client)
    assert_status(r5, 200)

    print("✅ auth tests passed")


if __name__ == "__main__":
    with httpx.Client(timeout=10) as client:
        if not server_is_up(client):
            raise SystemExit("Server not running")

        test_auth_register_login_logout(client)