import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import User, Vehicle, FuelLog, ServiceLog, Document
from app.routes import (
    auth,
    documents,
    fuel_logs,
    internal,
    maintenance_guidelines,
    service_logs,
    users,
    vehicles,
)
from app.utils.observability import (
    RequestContextMiddleware,
    RequestIdLogFilter,
)
from app.utils.rate_limiter import user_rate_limit
from app.utils.redis_client import close_redis, get_redis

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """
    Dev: default INFO. Production: WARNING for noisy libs, but keep
    ridecare.access at INFO so request-id structured logs stay visible.
    """
    root_level = logging.INFO if settings.APP_ENV == "development" else logging.WARNING
    logging.basicConfig(level=root_level, force=True)
    request_id_filter = RequestIdLogFilter()
    root = logging.getLogger()
    root.addFilter(request_id_filter)
    for handler in root.handlers:
        handler.addFilter(request_id_filter)
        handler.setFormatter(
            logging.Formatter(
                "%(levelname)s %(name)s [request_id=%(request_id)s] %(message)s"
            )
        )

    access = logging.getLogger("ridecare.access")
    access.setLevel(logging.INFO)
    access.propagate = True

    for name in ("sqlalchemy.engine", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).setLevel(logging.WARNING)


_configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await close_redis()


# Create FastAPI app
# redirect_slashes=False: behind the Vercel /api proxy, slash redirects would
# point at onrender.com and escape the same-origin cookie jar.
app = FastAPI(
    title="RideCare",
    description="A personal vehicle companion app for riders",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Add CORS middleware
# Normalize origins: trim whitespace/quotes and drop trailing slashes so
# browser Origin (no slash) matches env values that may include one.
_allowed_origins = [
    origin.strip().strip("\"'").rstrip("/")
    for origin in settings.ALLOWED_ORIGINS.split(",")
    if origin.strip()
]

# Last added = outermost. Request context wraps CORS so every response
# (including preflight) can carry X-Request-ID when it reaches the app stack.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestContextMiddleware)


@app.middleware("http")
async def general_rate_limit_middleware(request: Request, call_next):
    """
    User-based rate limiting for all authenticated API endpoints.
    Auth endpoints handle their own IP-based limiting.
    Health and docs endpoints are skipped entirely.
    """
    skip_paths = {"/health", "/docs", "/openapi.json", "/redoc"}
    skip_prefixes = ("/auth/", "/internal/")

    path = request.url.path

    if path not in skip_paths and not any(
        path.startswith(p) for p in skip_prefixes
    ):
        try:
            redis = get_redis()
            await user_rate_limit(request, redis)
        except Exception as e:
            if hasattr(e, "status_code") and e.status_code == 429:
                return JSONResponse(
                    status_code=429,
                    content={"detail": e.detail},
                    headers=e.headers or {},
                )
            logger.warning("Rate limiter error: %s", e)

    return await call_next(request)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"message": "OK", "environment": settings.APP_ENV}


app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(fuel_logs.router)
app.include_router(service_logs.router)
app.include_router(documents.router)
app.include_router(users.router)
app.include_router(maintenance_guidelines.router)
app.include_router(internal.router)
