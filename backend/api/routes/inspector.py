import os
import json
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Response
from datetime import datetime
from typing import Dict, Any, List
import yaml
from dotenv import load_dotenv
import logging
from utils.validators import validate_file, validate_postman_collection
from api.dependencies import get_llm_service
from api.services.llm_service import LLMService
from config.logging import setup_logging

# Setup logging
setup_logging()
load_dotenv()
logger = logging.getLogger(__name__)
router = APIRouter()

# Environment variables
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default

# Pydantic models
class PostmanCollectionRequest(BaseModel):
    info: Dict[Any, Any]
    item: List[Dict[Any, Any]]

class OpenAPIRequest(BaseModel):
    spec: Dict[Any, Any]

@router.post("/inspect")
async def inspect_file(file: UploadFile = File(...), llm_service: LLMService = Depends(get_llm_service)):
    """Upload and fix OpenAPI/YAML files"""
    logger.info(f"Received file: {file.filename}")
    
    # Validate file
    if not file.filename or not file.filename.lower().endswith(('.yaml', '.yml', '.json')):
        raise HTTPException(status_code=400, detail="File must be YAML (.yaml, .yml) or JSON (.json)")
    
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_FILE_SIZE/1024/1024:.1f}MB)")

    # Read and process
    try:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")
        
        validate_file(file_content)  # Basic validation (non-blocking)
        corrections = llm_service.get_corrections(file_content)
        
        return Response(
            content=corrections["corrected_spec"],
            status_code=200,
            media_type="application/x-yaml",
            headers={"Content-Disposition": f"attachment; filename=corrected-{file.filename}.yaml"}
        )
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=400, detail=f"Processing failed: {str(e)}")

@router.post("/inspect/postman")
async def inspect_postman_json(
    request: PostmanCollectionRequest, 
    llm_service: LLMService = Depends(get_llm_service)
):
    """Convert Postman collection to OpenAPI (returns JSON response)"""
    logger.info("Converting Postman collection to OpenAPI")
    
    try:
        # Convert request to collection dict
        collection = request.dict()  # Now request IS the collection
        
        # Validate Postman structure
        if not validate_postman_collection(collection):
            raise HTTPException(status_code=400, detail="Invalid Postman collection structure")
        
        # Convert with LLM
        collection_json = json.dumps(collection, indent=2)
        enhanced_prompt = _create_postman_conversion_prompt(collection_json)
        corrections = await _convert_postman_with_llm(llm_service, enhanced_prompt, collection_json)
        
        return {
            "status": "success",
            "collection_name": collection.get("info", {}).get("name", "Unknown"),
            "items_processed": len(collection.get("item", [])),
            "timestamp": datetime.utcnow().isoformat(),
            "suggestions": corrections.get("suggestions", ""),      
            "corrected_spec": corrections.get("corrected_spec", ""),
            "usage_tip": "Copy 'corrected_spec' and paste into swagger editor"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Postman conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@router.post("/inspect/postman/yaml")
async def inspect_postman_yaml(
    request: PostmanCollectionRequest, 
    llm_service: LLMService = Depends(get_llm_service)
):
    """Convert Postman collection to OpenAPI (returns downloadable YAML)"""
    logger.info("Converting Postman collection to OpenAPI YAML")
    
    try:
        # Convert request to collection dict  
        collection = request.dict()  # Now request IS the collection
        
        # Validate Postman structure
        if not validate_postman_collection(collection):
            raise HTTPException(status_code=400, detail="Invalid Postman collection structure")
        
        # Convert with LLM
        collection_json = json.dumps(collection, indent=2)
        enhanced_prompt = _create_postman_conversion_prompt(collection_json)
        corrections = await _convert_postman_with_llm(llm_service, enhanced_prompt, collection_json)
        
        collection_name = collection.get("info", {}).get("name", "postman-collection")
        filename = f"{collection_name.lower().replace(' ', '-')}-openapi.yaml"
        
        return Response(
            content=corrections["corrected_spec"],
            status_code=200,
            media_type="application/x-yaml",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Postman YAML conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@router.post("/inspect/openapi")
async def inspect_openapi_json(
    request: OpenAPIRequest, 
    llm_service: LLMService = Depends(get_llm_service)
):
    """Fix OpenAPI spec from JSON body"""
    logger.info("Processing OpenAPI spec from JSON")
    
    try:
        # Convert and validate
        spec_json = json.dumps(request.spec, indent=2)
        file_content = spec_json.encode('utf-8')
        
        is_valid = validate_file(file_content)  # Basic validation
        corrections = llm_service.get_corrections(file_content)

        return {
            "status": "success",
            "spec_title": request.spec.get("info", {}).get("title", "Unknown"),
            "spec_version": request.spec.get("openapi", request.spec.get("swagger", "Unknown")),
            "timestamp": datetime.utcnow().isoformat(),
            "validation_passed": is_valid,
            "suggestions": corrections.get("suggestions", ""),      
            "corrected_spec": corrections.get("corrected_spec", "")
        }
    except Exception as e:
        logger.error(f"OpenAPI processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Helper functions
def _create_postman_conversion_prompt(collection_json: str) -> str:
    """Create Postman to OpenAPI conversion prompt"""
    return f"""
You are an expert at converting Postman collections to OpenAPI 3.1.0 specifications.

Convert this Postman collection to a complete, valid OpenAPI 3.1.0 YAML specification:

REQUIREMENTS:
- Extract API info from collection.info
- Convert collection.item[] to OpenAPI paths
- Extract servers from request URLs
- Add security schemes based on auth types
- Include standard error responses (400, 401, 403, 404, 500)

MUST INCLUDE:
- openapi: 3.1.0
- Complete info, servers, paths, components sections
- Proper YAML structure (no duplicate keys)

Format response as:
## SUGGESTIONS:
[List of conversion decisions made]

## CORRECTED SPEC:
```yaml
[Complete OpenAPI 3.1.0 YAML]
```

Postman Collection:
```json
{collection_json}
```
"""

async def _convert_postman_with_llm(llm_service: LLMService, prompt: str, collection_json: str) -> dict:
    """Convert Postman collection using LLM"""
    if not llm_service.anthropic_client:
        return {"suggestions": "Error: No Claude API key configured", "corrected_spec": ""}
    
    try:
        max_tokens = llm_service.calculate_max_tokens(collection_json)
        
        response = llm_service.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        full_response = response.content[0].text
        return llm_service._parse_claude_response(full_response)
        
    except Exception as e:
        logger.error(f"LLM conversion failed: {e}")
        return {"suggestions": f"AI conversion failed: {str(e)}", "corrected_spec": ""}