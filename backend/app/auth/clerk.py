import jwt
from jwt import PyJWKClient

from app.config import settings

_jwks_client: PyJWKClient | None = None


def get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.clerk_jwks_url, cache_keys=True)
    return _jwks_client


async def verify_clerk_token(token: str) -> dict:
    """Verify a Clerk-issued JWT and return its payload.

    Returns dict with 'sub' (Clerk user ID) and other claims.
    Raises jwt.InvalidTokenError on failure.
    """
    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False},  # Clerk tokens may not have audience
    )
    return payload
