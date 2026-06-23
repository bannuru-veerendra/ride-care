from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import auth, vehicles

# Create FastAPI app
app = FastAPI(title="RideCare", description="A personal vehicle companion app for riders", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
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