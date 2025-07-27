"""
Fast API : OpenAPI/Swagger specification validation and correction tool that integrates 
with Postman and uses Claude/GPT for intelligent corrections.

"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from api.routes import health 
import logging


# Now we can import from config
from config.logging import setup_logging

setup_logging()
load_dotenv()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan():
    logger.info("Starting Spec Inspector API...")

    try:
        logger.info("Add Spec Inspector API Loigc here...")

        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        yield  # Still start the app even if there are issues
    finally:
        # Shutdown
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
#app.include_router(validation.router, prefix="/api/v1", tags=["validation"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Spec Inspector API",
        "version": "1.0.0",
        "docs": "/docs"
    }


