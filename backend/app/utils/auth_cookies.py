"""HttpOnly cookie helpers for access + refresh tokens."""

from fastapi import Response

from app.config import settings

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _cookie_flags() -> dict:
    """
    Cross-site (Vercel → Render) needs SameSite=None; Secure.
    Localhost Vite → API is same-site across ports, so Lax + insecure is fine.
    """
    is_prod = settings.APP_ENV == "production"
    return {
        "httponly": True,
        "secure": is_prod,
        "samesite": "none" if is_prod else "lax",
    }


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    flags = _cookie_flags()
    # path="/" so cookies work both for direct API hosts and same-origin
    # proxies (e.g. Vercel /api → Render). Refresh is only *used* on /auth/*.
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        **flags,
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
        **flags,
    )


def clear_auth_cookies(response: Response) -> None:
    flags = _cookie_flags()
    response.delete_cookie(key=ACCESS_COOKIE, path="/", **flags)
    response.delete_cookie(key=REFRESH_COOKIE, path="/", **flags)
    # Also clear any legacy refresh cookies scoped to /auth
    response.delete_cookie(key=REFRESH_COOKIE, path="/auth", **flags)
