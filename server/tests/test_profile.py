import os
import uuid
from typing import Optional, Dict, Any, Tuple

import httpx

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")


# ----------------------------
# Utilities
# ----------------------------
def _u(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def assert_status(resp: httpx.Response, expected: int, msg: str = ""):
    if resp.status_code != expected:
        raise AssertionError(
            f"{msg}\nExpected {expected}, got {resp.status_code}\nBody: {resp.text}"
        )


def pretty(resp: httpx.Response) -> str:
    return f"{resp.status_code} {resp.text}"


def auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def is_json(resp: httpx.Response) -> bool:
    return resp.headers.get("content-type", "").lower().startswith("application/json")


def j(resp: httpx.Response) -> Any:
    return resp.json() if is_json(resp) else None


def server_is_up(client: httpx.Client) -> bool:
    for path in ("/openapi.json", "/docs", "/"):
        try:
            r = client.get(f"{BASE_URL}{path}")
            if r.status_code in (200, 302):
                return True
        except Exception:
            pass
    return False


def try_server_reset(client: httpx.Client) -> bool:
    try:
        r = client.post(f"{BASE_URL}/api/test/reset", timeout=10)
        return r.status_code == 200
    except Exception:
        return False


# ----------------------------
# API helpers
# ----------------------------
def api_register(
    client: httpx.Client,
    email: str,
    password: str,
    name: Optional[str] = None,
    school: Optional[str] = None,
    current_location: Optional[str] = None,
    anchor_location: Optional[str] = None,
    budget: Optional[float] = None,
    preferences: Optional[list[str]] = None,
) -> Tuple[httpx.Response, Any]:
    r = client.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "email": email,
            "password": password,
            "name": name,
            "school": school,
            "current_location": current_location,
            "anchor_location": anchor_location,
            "budget": budget,
            "preferences": preferences or [],
        },
    )
    return r, j(r)


def api_get_profile(client: httpx.Client, token: str) -> httpx.Response:
    return client.get(
        f"{BASE_URL}/api/auth/profile",
        headers=auth_headers(token),
    )


def api_update_profile(client: httpx.Client, token: str, patch: Dict[str, Any]) -> httpx.Response:
    return client.patch(
        f"{BASE_URL}/api/auth/profile",
        json=patch,
        headers=auth_headers(token),
    )


# ----------------------------
# Tests
# ----------------------------
def test_profile_get_and_update(client: httpx.Client):
    email = f"{_u('profile')}@example.com"
    password = "Password123!"

    r, data = api_register(
        client,
        email,
        password,
        name="Profile User",
        school="Vanderbilt",
        current_location="Nashville",
        anchor_location="Chicago",
        budget=50.0,
        preferences=["coffee", "food"],
    )
    assert_status(r, 201, "Register failed")
    token = data["access_token"]

    # Initial GET
    rg = api_get_profile(client, token)
    assert_status(rg, 200, "Get profile failed")
    profile = rg.json()

    assert profile["email"] == email
    assert profile["name"] == "Profile User"
    assert profile["school"] == "Vanderbilt"
    assert profile["current_location"] == "Nashville"
    assert profile["anchor_location"] == "Chicago"
    assert profile["budget"] == 50.0
    assert profile["preferences"] == ["coffee", "food"]
    assert profile["email_verified"] is False

    # Partial update
    ru = api_update_profile(
        client,
        token,
        {
            "current_location": "Evanston",
            "budget": 80.0,
            "preferences": ["music", "sports", "late-night food"],
        },
    )
    assert_status(ru, 200, "Partial profile update failed")
    updated = ru.json()

    assert updated["name"] == "Profile User"
    assert updated["school"] == "Vanderbilt"
    assert updated["current_location"] == "Evanston"
    assert updated["anchor_location"] == "Chicago"
    assert updated["budget"] == 80.0
    assert updated["preferences"] == ["music", "sports", "late-night food"]
    assert updated["email_verified"] is False

    # Full follow-up update
    ru2 = api_update_profile(
        client,
        token,
        {
            "name": "Updated User",
            "school": "Northwestern",
            "anchor_location": "New York",
        },
    )
    assert_status(ru2, 200, "Second profile update failed")
    updated2 = ru2.json()

    assert updated2["name"] == "Updated User"
    assert updated2["school"] == "Northwestern"
    assert updated2["current_location"] == "Evanston"
    assert updated2["anchor_location"] == "New York"
    assert updated2["budget"] == 80.0
    assert updated2["preferences"] == ["music", "sports", "late-night food"]

    # Verify persistence
    rg2 = api_get_profile(client, token)
    assert_status(rg2, 200, "Get profile after update failed")
    profile2 = rg2.json()

    assert profile2["name"] == "Updated User"
    assert profile2["school"] == "Northwestern"
    assert profile2["current_location"] == "Evanston"
    assert profile2["anchor_location"] == "New York"
    assert profile2["budget"] == 80.0
    assert profile2["preferences"] == ["music", "sports", "late-night food"]

    # Unauthorized GET
    rbad = client.get(f"{BASE_URL}/api/auth/profile")
    if rbad.status_code not in (401, 403):
        raise AssertionError(f"Expected 401/403 for unauthorized profile get, got {pretty(rbad)}")

    # Unauthorized PATCH
    rbad2 = client.patch(f"{BASE_URL}/api/auth/profile", json={"name": "Hacker"})
    if rbad2.status_code not in (401, 403):
        raise AssertionError(f"Expected 401/403 for unauthorized profile patch, got {pretty(rbad2)}")

    print("✅ test_profile_get_and_update passed")


if __name__ == "__main__":
    with httpx.Client(timeout=10) as client:
        if not server_is_up(client):
            raise SystemExit(
                f"Server not reachable at {BASE_URL}. Start it then rerun."
            )

        reset_ok = try_server_reset(client)
        if reset_ok:
            print("🧼 Server DB reset via /api/test/reset")

        test_profile_get_and_update(client)

        print("\n🎉 Profile tests passed")