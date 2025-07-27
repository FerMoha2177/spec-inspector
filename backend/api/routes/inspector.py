import os
import sys 
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from datetime import datetime
from typing import Optional
import yaml
from dotenv import load_dotenv
import logging
from utils.validators import validate_file
from api.services.llm_service import LLMService

from config.logging import setup_logging
# Setup logging
setup_logging()

logger = logging.getLogger(__name__)

router = APIRouter()

# Load environment variables with defaults
load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
PROCESSED_DIR = os.getenv("PROCESSED_DIR", "./processed")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default

@router.post("/inspect")
async def inspect(file: UploadFile = File(...)):
    """
    Inspect and validate OpenAPI specification file
    Returns validation results and corrections if needed
    """
    logger.info(f"Received file: {file.filename}")
    
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(('.yaml', '.yml')):
        raise HTTPException(
            status_code=400, 
            detail="File must be a YAML file (.yaml or .yml extension)"
        )

    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File size must be less than {MAX_FILE_SIZE/1024/1024}MB"
        )

    # Read file content
    try:
        file_content = await file.read()  # ✅ Use await for async read
        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")
            
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Validate file structure using your validator
    try:
        is_valid = validate_file(file_content)  # ✅ Pass bytes directly
        if not is_valid:
            raise HTTPException(status_code=400, detail="File structure is not valid OpenAPI format")


    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")

    # TODO: Add more validation layers here
    # Layer 1: YAML format ✅ (handled above)
    # Layer 2: Basic metadata ✅ (in validate_file)
    # Layer 3: OpenAPI detection
    # Layer 4: Version-specific validation
    # Layer 5: Claude correction
    
    try:    
        llm_service = LLMService()
        corrections = llm_service.get_corrections(file_content)
    except Exception as e:
        logger.error(f"LLM correction failed: {e}")
        raise HTTPException(status_code=400, detail=f"LLM correction error: {str(e)}")
    
    return {
        "status": "success",
        "filename": file.filename,
        "file_size": len(file_content),
        "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
        "validation_passed": is_valid,
        "corrections": corrections,
    }