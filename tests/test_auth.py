from datetime import UTC, datetime, timedelta
from typing import Annotated, cast

import pytest
from fastapi import Depends, FastAPI, Security
from fastapi.testclient import TestClient
from jose import jwt

from fapilot.auth import AuthenticationResult, create_access_token, get_current_user, optional_user
from fapilot.conf import FapilotSettings
from fapilot.core.application import create_app


async def verify_basic(request, username, password):
    if (username, password) == ("alice", "secret"):
        return AuthenticationResult("alice", frozenset({"read"}))
    return None


async def verify_key(request, token):
    if token == "valid-key":
        return AuthenticationResult("service")
    return None


def client_for(backends, **kwargs):
    settings = FapilotSettings(
        SECRET_KEY="test-secret-" * 4, AUTHENTICATION_BACKENDS=backends, **kwargs
    )
    app = create_app(settings)

    @app.get("/private")
    async def private(user: Annotated[str, Depends(get_current_user)]):
        return {"user": user}

    @app.get("/optional")
    async def optional(user: Annotated[str | None, Depends(optional_user)]):
        return {"user": user}

    @app.get("/scoped")
    async def scoped(user: Annotated[str, Security(get_current_user, scopes=["read"])]):
        return {"user": user}

    return TestClient(app), settings


BASIC = {
    "backend": "fapilot.auth.BasicBackend",
    "options": {"verifier": "tests.test_auth.verify_basic"},
}
KEY = {
    "backend": "fapilot.auth.APIKeyBackend",
    "options": {"verifier": "tests.test_auth.verify_key"},
}


def test_basic_and_scopes():
    client, _ = client_for([BASIC])
    assert client.get("/private").status_code == 401
    assert client.get("/optional").json() == {"user": None}
    assert client.get("/scoped", auth=("alice", "secret")).status_code == 200
    response = client.get("/optional", auth=("alice", "wrong"))
    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic")


@pytest.mark.parametrize("value", ["Basic", "Basic !!!", "Basic YWxpY2U=", "Basic a b"])
def test_malformed_basic(value):
    client, _ = client_for([BASIC, KEY])
    assert (
        client.get(
            "/private", headers={"Authorization": value, "X-API-Key": "valid-key"}
        ).status_code
        == 401
    )


def test_api_key_and_order():
    client, _ = client_for([BASIC, KEY])
    assert client.get("/private", headers={"X-API-Key": "valid-key"}).json() == {"user": "service"}
    assert client.get("/scoped", headers={"X-API-Key": "valid-key"}).status_code == 403
    assert client.get("/private", headers={"X-API-Key": "bad"}).status_code == 401
    assert (
        client.get(
            "/private", headers=[("X-API-Key", "valid-key"), ("X-API-Key", "bad")]
        ).status_code
        == 401
    )


def test_jwt_and_app_isolation():
    client, settings = client_for(["fapilot.auth.JWTBackend"])
    token = create_access_token("alice", {"scope": "read"}, settings=settings)
    assert client.get("/scoped", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    other, _ = client_for(["fapilot.auth.JWTBackend"], JWT_SETTINGS={"issuer": "other"})
    assert other.get("/private", headers={"Authorization": f"Bearer {token}"}).status_code == 401


@pytest.mark.parametrize(
    "change",
    [
        {"exp": 1},
        {"exp": {}},
        {"nbf": []},
        {"iss": "wrong"},
        {"sub": ""},
        {"scope": ["read"]},
        {"exp": None},
        {"sub": None},
        {"iss": None},
        {"aud": "wrong"},
    ],
)
def test_jwt_rejections(change):
    client, settings = client_for(["fapilot.auth.JWTBackend"])
    claims = {"sub": "alice", "iss": "fapilot", "exp": datetime.now(UTC) + timedelta(minutes=1)}
    claims.update(change)
    claims = {k: v for k, v in claims.items() if v is not None}
    token = jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")
    assert client.get("/private", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_opaque_token():
    client, _ = client_for(
        [
            {
                "backend": "fapilot.auth.TokenBackend",
                "options": {"verifier": "tests.test_auth.verify_key"},
            }
        ]
    )
    assert client.get("/private", headers={"Authorization": "Bearer valid-key"}).status_code == 200


def test_configuration_errors():
    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app(FapilotSettings(AUTHENTICATION_BACKENDS=["fapilot.auth.JWTBackend"]))
    with pytest.raises(ValueError, match="Reserved"):
        create_access_token(
            "alice",
            {"exp": 1},
            settings=FapilotSettings(SECRET_KEY="secret"),
        )


def test_audience_and_signature():
    client, settings = client_for(["fapilot.auth.JWTBackend"], JWT_SETTINGS={"audience": "my-api"})
    token = create_access_token("alice", settings=settings)
    assert client.get("/private", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    other = FapilotSettings(SECRET_KEY="different-secret")
    token = create_access_token("alice", settings=other)
    assert client.get("/private", headers={"Authorization": f"Bearer {token}"}).status_code == 401


async def counted_verifier(request, token):
    request.state.calls = getattr(request.state, "calls", 0) + 1
    return AuthenticationResult("alice")


def test_authentication_is_cached_per_request():
    from fastapi import Request

    client, _ = client_for(
        [
            {
                "backend": "fapilot.auth.TokenBackend",
                "options": {"verifier": "tests.test_auth.counted_verifier"},
            }
        ]
    )

    @cast(FastAPI, client.app).get("/cached")
    async def cached(
        request: Request,
        first: Annotated[str, Depends(optional_user)],
        second: Annotated[str, Depends(get_current_user)],
    ):
        return {"calls": request.state.calls}

    for _ in range(2):
        assert client.get("/cached", headers={"Authorization": "Bearer test"}).json() == {
            "calls": 1
        }
