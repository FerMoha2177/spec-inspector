import sys
import os
import logging
from dotenv import load_dotenv
from config.logging import setup_logging
import yaml

# Setup logging
setup_logging()
load_dotenv()

logger = logging.getLogger(__name__)

def validate_file(file_content: bytes) -> bool:
    """
    Validate that file content contains basic OpenAPI structure
    """
    try:
        # Convert bytes to string
        content_str = file_content.decode('utf-8')
        
        if not content_str.strip():
            logger.error("File content is empty")
            return False
            
        # Parse YAML
        try:
            spec = yaml.safe_load(content_str)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML syntax: {e}")
            return False
            
        if not spec or not isinstance(spec, dict):
            logger.error("File does not contain valid YAML object")
            return False
            
        return validate_basic_info(spec)
        
    except UnicodeDecodeError as e:
        logger.error(f"File encoding error: {e}")
        return False
    except Exception as e:
        logger.error(f"Could not validate file: {e}")
        return False

def validate_basic_info(spec: dict) -> bool:
    """
    Check for basic OpenAPI/Swagger structure
    """
    try:
        logger.info("Validating basic OpenAPI structure...")
        
        # Check for OpenAPI version indicators
        has_openapi = 'openapi' in spec
        has_swagger = 'swagger' in spec
        
        if not (has_openapi or has_swagger):
            logger.error("Missing 'openapi' or 'swagger' version field")
            return False
            
        # Check for required info section
        if 'info' not in spec:
            logger.error("Missing required 'info' section")
            return False
            
        info = spec['info']
        if not isinstance(info, dict):
            logger.error("'info' section must be an object")
            return False
            
        # Check required info fields
        required_info_fields = ['title', 'version']
        for field in required_info_fields:
            if field not in info:
                logger.error(f"Missing required info field: {field}")
                return False
                
        # Check for paths (can be empty object)
        if 'paths' not in spec:
            logger.error("Missing required 'paths' section")
            return False
            
        logger.info("Basic validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Basic validation error: {e}")
        return False