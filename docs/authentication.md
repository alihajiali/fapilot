# API authentication

[Documentation index](index.md)

Configure an ordered list in your settings module. Authentication is opt-in per route;
existing public endpoints stay public. Backend instances are created when the app is built,
and receive that application's settings.

```python
SECRET_KEY = "load-a-long-random-secret-from-your-environment"
AUTHENTICATION_BACKENDS = [
    {"backend": "fapilot.auth.JWTBackend", "options": {
        "user_loader": "users.auth.load_user",
    }},
    {"backend": "fapilot.auth.BasicBackend", "options": {
        "verifier": "users.auth.verify_login",
    }},
    {"backend": "fapilot.auth.APIKeyBackend", "options": {
        "verifier": "users.auth.verify_api_key", "header": "X-API-Key",
    }},
]
JWT_SETTINGS = {"issuer": "my-service", "audience": "my-api"}
```

A backend with no options can be specified as a dotted string. The default list is empty.
Configuration also works through Pydantic's JSON environment settings.

## Protect endpoints

```python
from typing import Annotated
from fastapi import APIRouter, Depends, Security
from fapilot.auth import get_current_user, optional_user

router = APIRouter()

@router.get("/me")
async def me(user: Annotated[object, Depends(get_current_user)]):
    return {"id": str(user.id)}

@router.get("/reports")
async def reports(user: Annotated[object, Security(get_current_user, scopes=["reports:read"])]):
    return {"allowed": True}
```

Use `Depends(optional_user)` to accept anonymous requests. Supplied invalid credentials
still produce 401. Missing credentials on protected routes produce 401 and a
`WWW-Authenticate` challenge; missing scopes produce 403. Results are cached once per
request and exposed as `request.state.user` and `request.state.auth`. `IsAuthenticated`
uses the same authentication manager. Authentication runs only when these dependencies
or permissions are invoked. Public routes without them do not parse credentials.

The generic dependency enforces `Security` scopes at runtime. It does not automatically
add backend-specific OpenAPI security schemes or Swagger Authorize controls.

## Identity and credential hooks

Hooks are async functions imported from dotted paths. They own database lookup, account
status, token revocation, and provider calls; the framework does not assume a user schema.
`AUTH_USER_MODEL` is not automatically queried by these backends.

```python
from fapilot.auth import AuthenticationResult

async def load_user(request, claims):
    # Adapt to your actual model; return None for a deleted or disabled user.
    return await User.get_or_none(id=claims["sub"], is_active=True)

async def verify_login(request, username, password):
    user = await your_password_service.verify(username, password)
    if user is None:
        return None
    return AuthenticationResult(user, frozenset({"reports:read"}))

async def verify_api_key(request, token):
    account = await your_key_store.lookup_valid_key(token)
    if account is None:
        return None
    return AuthenticationResult(account, frozenset({"reports:read"}))
```

`User`, `your_password_service`, and `your_key_store` above are application-owned services.
Use HTTPS for credentials. Store API-key digests, use constant-time comparisons where
applicable, and rate-limit credential verification. Run blocking password verification
in a worker thread. Hooks return `AuthenticationResult` or `None`; backend results with
`user=None` or an object's `is_active=False` are rejected. Hook failures propagate as
server errors instead of being silently treated as anonymous requests.

JWT's optional `user_loader(request, claims)` returns the user directly. Without it,
the authenticated user is the subject string; no database status or revocation check
occurs. JWT scopes come from a space-separated `scope` claim.

## JWT issuance and validation

```python
from fapilot.auth import create_access_token

token = create_access_token(
    str(user.id), {"scope": "reports:read"}, settings=request.app.state.fapilot.settings
)
```

Existing calls without `settings=` use the global settings loader. Pass explicit settings
when running multiple applications. Tokens require a nonempty subject, expiry and the
configured issuer; audience is checked when configured. Reserved `sub`, `iss`, `exp`,
and `aud` claims cannot be overridden during issuance. The default `change-me` key
is rejected. Existing tokens missing the required claims will no longer validate.

`JWT_SETTINGS` supports `algorithm`, `issuer`, `audience`, `access_token_expire_minutes`,
`verification_key`, and nonnegative `leeway` (seconds). For asymmetric signing,
`SECRET_KEY` holds the private signing key and `verification_key` the public key.
Only the configured algorithm is accepted. Refresh tokens, logout/revocation storage,
JWKS rotation and OAuth login redirects are application responsibilities.

## Opaque tokens and custom backends

`fapilot.auth.TokenBackend` accepts `verifier` and an optional `scheme` (default `Bearer`).
Its async verifier receives `(request, token)` and returns `AuthenticationResult` or
`None`. This supports database tokens and OAuth introspection adapters; your adapter
must validate provider responses, expiration, audience and scopes.

Backends run in settings order. The first success wins. An absent or unrelated credential
returns `None`; a matching but invalid credential raises `AuthenticationError` and stops
the chain. JWT and opaque Bearer backends therefore should not be chained as fallbacks
for invalid tokens. Use separate schemes or a custom dispatcher for mixed token formats.

```python
from fapilot.auth import AuthenticationBackend, AuthenticationError, AuthenticationResult

class CustomBackend(AuthenticationBackend):
    challenge = "Custom"

    async def authenticate(self, request):
        credential = request.headers.get("X-Custom-Credential")
        if credential is None:
            return None
        identity = await validate_custom_credential(credential)
        if identity is None:
            raise AuthenticationError(self.challenge)
        return AuthenticationResult(identity)
```

Register its dotted path in `AUTHENTICATION_BACKENDS`. Instances are shared: never store
request-specific state on the backend. Custom options are passed to the constructor
alongside `settings`. Cookie/session auth, signed requests and trusted client-certificate
identities can be implemented with this contract; cookie auth must include CSRF protection.
For a plain FastAPI app, install `AuthenticationManager(settings)` on
`app.state.authentication` before using the dependencies.

Design references: [FastAPI security scopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
and [Starlette authentication backends](https://starlette.dev/authentication/).

## Password helpers

```python
from fapilot.auth import hash_password, verify_password

# Run with a validated compatible Passlib/bcrypt dependency combination.
hashed = hash_password("example-password")
assert verify_password("example-password", hashed)
assert not verify_password("incorrect-password", hashed)
```

Both functions are synchronous wrappers around a Passlib bcrypt context. Store the
hash, never the plaintext password. Hashing is CPU work; account for that when calling
it from async request handlers. The wrappers do not translate backend errors.

**Verified compatibility limitation:** validation with Passlib 1.7.4 and bcrypt 5.0.0
failed to hash a short password. Passlib logged a missing `bcrypt.__about__` attribute,
then raised a 72-byte password error during its backend check. The current dependency
ranges permit this combination. Validate and lock a working combination in your
application environment before relying on these helpers; the short-password failure
is not fixed by truncating the user's password. The dependency constraint is unchanged
by this documentation update.


## Custom permissions

Implement `async has_permission(request) -> bool` and invoke
`fapilot.permissions.base.require_permissions(request, *permissions)` in a dependency.
It checks permissions in order and raises 403 on denial. `AllowAny` always passes;
`IsAuthenticated` resolves the configured authentication backends. Object ownership
and tenant checks remain application responsibilities.
