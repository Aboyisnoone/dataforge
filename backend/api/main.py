import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import datasets, investigations
from backend.persistence.database import engine, Base
import backend.persistence.models  # Important for metadata registry
from core.config import settings
from core.telemetry import setup_telemetry, telemetry_middleware
from starlette.middleware.base import BaseHTTPMiddleware

setup_telemetry()

Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DataForge API",
    description="Thin API adapter for DataForge core engine",
    version="1.1.0"
)

# Add Telemetry middleware first so it times everything
app.add_middleware(BaseHTTPMiddleware, dispatch=telemetry_middleware)

allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(investigations.router)

@app.on_event("startup")
def startup_event():
    # Validate Copilot configurations at startup
    if not settings.GEMINI_API_KEY:
        logger.warning(
            "GEMINI_API_KEY is not set in the environment or .env file. "
            "DataForge Copilot endpoints will return 500s until configured."
        )
    else:
        logger.info("DataForge Copilot initialized successfully.")

@app.get("/")
def root():
    return {"status": "ok", "message": "DataForge API running"}
