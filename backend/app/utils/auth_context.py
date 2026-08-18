"""Per-request auth state shared by rate-limit middleware and get_current_user."""

from dataclasses import dataclass

from fastapi import Request

from app.utils.auth_cookies import ACCESS_COOKIE

_AUTH_HOT_PATH = "auth_hot_path"


@dataclass(frozen=True, slots=True)
class AuthHotPath:
    """Redis results from the rate-limit pipeline, reused by get_current_user."""

    payload: dict | None
    blocklisted: bool
    revoke_before: int | None
    cached_user: dict | None


def get_access_token_from_request(request: Request) -> str | None:
    """Bearer header first, then the httpOnly access cookie."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        if token:
            return token
    return request.cookies.get(ACCESS_COOKIE)


def get_auth_hot_path(request: Request) -> AuthHotPath | None:
    return getattr(request.state, _AUTH_HOT_PATH, None)


def set_auth_hot_path(request: Request, hot_path: AuthHotPath) -> None:
    setattr(request.state, _AUTH_HOT_PATH, hot_path)
