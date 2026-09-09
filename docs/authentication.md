# Authentication and permissions

[Documentation index](index.md)

Fapilot provides helper functions, not a complete authentication system. You supply
the user model, login routes, user lookup, authorization rules, token lifecycle,
and any refresh/revocation flow. `AUTH_USER_MODEL` is currently configuration only.

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

## Tokens

```python
from fapilot.auth import create_access_token, decode_access_token

token = create_access_token("123", claims={"role": "reader"})
payload = decode_access_token(token)
assert payload is not None
assert payload["sub"] == "123"
```

Issuance reads cached settings and adds `sub`, `iss`, and `exp`. The default algorithm
is HS256 and the default lifetime is 30 minutes. Additional claims are merged last,
so they can replace even these standard claims. Only pass server-controlled claims.

Decoding uses the configured secret and algorithm and returns a dictionary or `None`
when python-jose raises `JWTError`. The helper does not pass an expected issuer to
`jwt.decode`, require all application claims, or look up a user. If issuer/audience
validation is required, implement and test it explicitly. Keep `SECRET_KEY` consistent
with the settings used by all token consumers and replace the generated placeholder.

## Protect an endpoint

The following dependency authenticates a token, requires a subject, and populates
request state. Extend it with a database user lookup and active-user checks for a real
account system. Add it to your app's `api.py` or dependency module:

```python
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fapilot.auth import decode_access_token
from fapilot.permissions import IsAuthenticated
from fapilot.permissions.base import require_permissions

bearer = HTTPBearer(auto_error=False)


async def authenticated_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    payload = decode_access_token(credentials.credentials) if credentials else None
    if payload is None or not isinstance(payload.get("sub"), str) or not payload["sub"]:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.state.user = {"id": payload["sub"]}
    await require_permissions(request, IsAuthenticated())
    return request.state.user


# Attach to an existing APIRouter:
# @router.get("/me")
# async def me(user: dict = Depends(authenticated_user)):
#     return user
```

`IsAuthenticated` only checks whether `request.state.user` is not `None`; it does
not read the Authorization header or verify a token. `AllowAny` always passes.
`require_permissions(request, *permissions)` awaits every supplied permission in
order and raises HTTP 403 on the first denial. Import it from
`fapilot.permissions.base`; it is not re-exported by `fapilot.permissions`.

## Custom permissions

Implement `async has_permission(request) -> bool`. For example, a permission may
read a role from a previously authenticated user in request state. Permission classes
are not installed automatically when placed in `permissions.py`; invoke them from
an explicit dependency. Object ownership and tenant checks belong in your application.
