"""
Fast API : OpenAPI/Swagger specification validation and correction tool that integrates 
with Postman and uses Claude/GPT for intelligent corrections.
"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Import from relative modules
from api.routes import health, inspector
from config.logging import setup_logging

# Setup logging and load environment
setup_logging()
load_dotenv()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Spec Inspector API...")
    try:
        logger.info("Add Spec Inspector API Logic here...")
        yield
    except Exception as e:
        logger.error(f"Startup error: {e}")
        yield
    finally:
        logger.info("Shutting down API...")
        logger.info("API shutdown complete!")

# Create FastAPI app
app = FastAPI(
    title="Spec Inspector API",
    description="AI-powered API for correcting OpenAI/Swagger Specifications against Open API 3.1 Specifications",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(inspector.router, prefix="/api/v1", tags=["inspector"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Spec Inspector API",
        "version": "1.0.0",
        "docs": "/docs"
    }