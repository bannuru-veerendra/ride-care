from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import User, Vehicle, FuelLog, ServiceLog, Document
from app.routes import auth, fuel_logs, vehicles, service_logs, documents

# Create FastAPI app
app = FastAPI(
    title="RideCare",
    description="A personal vehicle companion app for riders",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.ALLOWED_ORIGINS.split(",")
        if origin.strip()
    ],
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
