import os
import sys 
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import logging

from config.logging import setup_logging
# Setup logging
setup_logging()


logger = logging.getLogger(__name__)

router = APIRouter()

router = APIRouter()
@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    Returns 200 OK if API is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "SpecInspector API"
    }