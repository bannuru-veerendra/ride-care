from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import User, Vehicle, FuelLog, ServiceLog, Document
from app.routes import auth, fuel_logs, vehicles, service_logs, documents
from app.utils.redis_client import close_redis


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await close_redis()


# Create FastAPI app
app = FastAPI(
    title="RideCare",
    description="A personal vehicle companion app for riders",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
# Normalize origins: trim whitespace/quotes and drop trailing slashes so
# browser Origin (no slash) matches env values that may include one.
_allowed_origins = [
    origin.strip().strip("\"'").rstrip("/")
    for origin in settings.ALLOWED_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"message": "OK", "environment": settings.APP_ENV}


app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(fuel_logs.router)
app.include_router(service_logs.router)
app.include_router(documents.router)
