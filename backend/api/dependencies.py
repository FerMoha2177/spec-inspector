"""
Dependency injection for FastAPI services
Provides centralized access to application services
"""

from fastapi import HTTPException
from typing import Optional
from config.logging import setup_logging
from api.services.llm_service import LLMService
import logging

setup_logging()
logger = logging.getLogger(__name__)

_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the LLM service instance"""
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService()
        logger.info("LLM service initialized")
    
    return _llm_service