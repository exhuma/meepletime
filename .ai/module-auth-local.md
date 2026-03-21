# Agent instructions: module-auth-local

> **WARNING — LOCAL AUTHENTICATION REQUIRES CAREFUL REVIEW**
>
> Implementing local username/password authentication introduces
> significant security responsibilities that external identity
> providers handle for you. Before implementing this module, the
> engineering lead must sign off on the following checklist. Record
> the sign-off date in `contract.md`.
>
> If OIDC is viable for this project, use `module-auth-oidc`
> instead.

---

## Pre-implementation checklist

All items below are mandatory. Do not write password hashing or
JWT issuance code until every item is documented in `contract.md`
as resolved.

- [ ] **Rate limiting** — login, registration, and password-reset
  endpoints must be rate-limited before or at deployment. Name the
  mechanism (e.g. nginx `limit_req`, a reverse proxy, application
  middleware).
- [ ] **Account enumeration prevention** — login failure messages
  must not reveal whether the email exists. Registration duplicate
  responses must not differ in timing from non-duplicate responses.
- [ ] **Email verification** — new accounts must be verified before
  they can authenticate. Document the outbound email provider.
- [ ] **Password-reset token security** — tokens are single-use,
  expire in ≤ 1 hour, stored as a hash (not plaintext), and
  invalidated on use or on any successful login.
- [ ] **Transport security** — plaintext HTTP must be rejected at
  deployment. Document where TLS termination occurs.

---

## Architecture invariants

- `client_secret` does not exist in this module — the project
  issues its own JWTs.
- FastAPI is stateless. No server-side session state. Every
  request carries a bearer token that is independently validated.
- The same `get_current_user` dependency shape used by
  `module-auth-oidc` must be preserved so the two modules can
  coexist without route-handler changes.

---

## Password hashing

### Package

```
uv add passlib[argon2] argon2-cffi
```

`argon2` is the required algorithm. `bcrypt` is **prohibited** —
it has a 72-byte input limit that is not consistently enforced
across libraries, silently truncating long passwords. `pbkdf2` is
**prohibited** without an explicit security review documented in
`contract.md`.

### Usage

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """Return an argon2 password hash.

    :param password: Plaintext password from the user.
    :returns: Argon2 hash string, safe to store.
    """
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored hash.

    :param plain: Password from the login form.
    :param hashed: Stored argon2 hash from the database.
    :returns: True if the password matches, False otherwise.
    ---
    Always call this function even when the account does not
    exist, using a dummy hash, to prevent timing-based
    enumeration attacks.
    """
    return pwd_context.verify(plain, hashed)
```

### Constant-time account-not-found protection

```python
_DUMMY_HASH = pwd_context.hash("dummy")

async def authenticate_user(email: str, password: str, db) -> User | None:
    user = await get_user_by_email(db, email)
    if user is None:
        # Run verification anyway to prevent timing oracle.
        pwd_context.verify(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
```

---

## JWT issuance

### Package

```
uv add pyjwt[crypto]
```

Same `pyjwt` used by `module-auth-oidc`. Do not import any other
JWT library.

### Signing key

```python
# app/config.py
SECRET_KEY: str          # minimum 64 hex characters (256-bit)
ALGORITHM: str = "HS256" # or RS256 with key rotation documented
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

Generate the secret with:

```
python -c "import secrets; print(secrets.token_hex(64))"
```

Never commit `SECRET_KEY` to version control.

### Token creation

```python
from datetime import datetime, timedelta, timezone
import jwt

def create_access_token(subject: str, settings) -> str:
    """Issue a short-lived access JWT.

    :param subject: User identifier (e.g. UUID as string).
    :param settings: Application configuration.
    :returns: Signed JWT string.
    ---
    Expiry is set to UTC now + ACCESS_TOKEN_EXPIRE_MINUTES.
    The 'sub' claim carries the user identifier only.
    No sensitive data (passwords, emails) is embedded.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
```

- Access tokens expire in ≤ 15 minutes.
- Refresh tokens must be stored as a hash in the database (same
  `pwd_context.hash` as passwords). Never store plaintext refresh
  tokens.
- Refresh token rotation: issue a new token and invalidate the
  old one on every use.

### Token validation dependency

```python
# app/auth/dependencies.py
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    settings = Depends(get_settings),
    db = Depends(get_db),
):
    """Validate a locally-issued bearer token.

    :param credentials: Authorization header value.
    :param settings: Application configuration.
    :param db: Database session.
    :returns: ORM User object.
    :raises HTTPException: 401 if token is invalid or expired.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        subject: str = payload.get("sub")
        if subject is None:
            raise ValueError("Missing sub claim")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user = await get_user_by_id(db, subject)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
```

---

## Required API endpoints

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register` | Hash password; verify email before activating |
| POST | `/auth/login` | Return access + refresh tokens; constant-time |
| POST | `/auth/refresh` | Validate stored refresh hash; rotate |
| POST | `/auth/logout` | Invalidate refresh token in DB |
| POST | `/auth/request-reset` | Send reset token; always 200 regardless |
| POST | `/auth/reset-password` | Validate + invalidate token; hash new password |

The `/auth/request-reset` endpoint must return HTTP 200 with an
identical body regardless of whether the email exists. The email
is dispatched asynchronously.

---

## Prohibited patterns

- **Security questions** — never implement.
- **SMS OTP as sole factor** — permitted only if documented in
  `contract.md` with a threat model acknowledging SIM-swap risk
  and a backup factor provided.
- **Parallel auth paths** — if `module-auth-oidc` is also installed,
  both authentication paths must share the same `get_current_user`
  dependency signature. Route handlers must not distinguish between
  locally-authenticated and OIDC-authenticated users.
- **Storing passwords in logs** — never log any field from a
  registration or login request body.
- **Plaintext reset tokens in DB** — store the hash; send the
  plaintext once via email only.

---

## Email verification

- Emit a signed, single-use verification token on registration.
- Expire verification tokens in ≤ 24 hours.
- Until verified: the user record exists but is inactive; logins
  return HTTP 403 with a "verify your email" message.
- Document the outbound provider (SendGrid, SES, SMTP) and
  document it in `docs/developer/integrations.md`.

---

## Testing

### Backend

- Unit-test `authenticate_user` with: valid credentials, wrong
  password, non-existent email (confirm no timing difference in
  assertion — use mock to assert `verify` was called).
- Test token expiry for both access and refresh tokens.
- Test refresh token rotation: used token cannot be re-used.
- Test reset token: expired, used, valid.
- Never use real passwords in test fixtures; use
  `pwd_context.hash("test-password")` in fixtures.

### Frontend

- Mock the `/auth/login` and `/auth/refresh` endpoints in vitest.
- Test that an expired access token triggers a refresh attempt.
- Test that a failed refresh redirects to the login page.
