import os
import sys 
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv
import logging
from api.dependencies import get_llm_service
from api.services.llm_service import LLMService

from config.logging import setup_logging
# Setup logging
setup_logging()

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    Returns 200 OK if API is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "SpecInspector API"
    }

@router.get("/health/detailed")  # ✅ Fixed typo: "detailed" not "deatiled"
async def detailed_health_check(llm_service: LLMService = Depends(get_llm_service)):
    """
    Detailed Health Endpoint for displaying LLM service data
    """
    try:
        # Get service information
        service_info = llm_service.get_service_info()
        
        # Test Claude connection
        connection_test = llm_service.test_connection()
        
        # System information
        system_info = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE", "10485760")) / 1024 / 1024,
        }
        
        # Determine overall health status
        overall_healthy = (
            service_info["claude_available"] and 
            service_info["api_key_configured"] and 
            connection_test["success"]
        )
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "SpecInspector API - Detailed Health Check",
            "services": {
                "llm_service": service_info,
                "claude_connection": connection_test
            },
            "system": system_info,
            "capabilities": {
                "file_validation": True,
                "openapi_correction": service_info["claude_available"],
                "supported_formats": [".yaml", ".yml"],
                "max_tokens": service_info.get("max_tokens_supported", "Unknown")
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "SpecInspector API - Health Check Failed",
            "error": str(e),
            "services": {
                "llm_service": {"available": False, "error": str(e)}
            }
        }

@router.get("/health/quick-test")
async def quick_test_endpoint(llm_service: LLMService = Depends(get_llm_service)):
    """
    Quick test endpoint to verify Claude is responding
    """
    try:
        test_result = llm_service.test_connection()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "test_result": test_result,
            "ready_for_requests": test_result["success"]
        }
        
    except Exception as e:
        logger.error(f"Quick test failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "test_result": {"success": False, "error": str(e)},
            "ready_for_requests": False
        }