import sys
import os
import json
import logging
from dotenv import load_dotenv
from config.logging import setup_logging
import yaml

# Setup logging
setup_logging()
load_dotenv()

logger = logging.getLogger(__name__)

def _convert_json_to_yaml(file_content: bytes) -> str:
    """
    Convert JSON bytes to YAML string
    """
    try:
        content_str = file_content.decode('utf-8')
        data = json.loads(content_str)  # Parse JSON from string, not file
        return yaml.dump(data, default_flow_style=False)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return ""
    except Exception as e:
        logger.error(f"Could not convert JSON to YAML: {e}")
        return ""

def _validate_json_file(file_content: bytes) -> bool:
    """
    Validate that the file content is valid JSON
    """
    try:
        content_str = file_content.decode('utf-8')
        json.loads(content_str)  # Just validate JSON parsing
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON syntax: {e}")
        return False
    except Exception as e:
        logger.error(f"Could not validate JSON file: {e}")
        return False

def _detect_file_type(file_content: bytes) -> str:
    """
    Detect if file content is JSON or YAML
    Returns: 'json', 'yaml', or 'unknown'
    """
    try:
        content_str = file_content.decode('utf-8').strip()
        
        # Try JSON first
        try:
            json.loads(content_str)
            return 'json'
        except json.JSONDecodeError:
            pass
        
        # Try YAML
        try:
            yaml.safe_load(content_str)
            return 'yaml'
        except yaml.YAMLError:
            pass
            
        return 'unknown'
        
    except Exception as e:
        logger.error(f"Could not detect file type: {e}")
        return 'unknown'

def validate_file(file_content: bytes) -> bool:
    """
    Validate that file content contains basic OpenAPI structure.
    Supports both JSON and YAML input files.
    
    Process:
    1. Detect file type (JSON or YAML)
    2. If JSON: convert to YAML, then validate
    3. If YAML: validate directly
    4. Check for basic OpenAPI structure
    """
    try:
        # Convert bytes to string
        content_str = file_content.decode('utf-8')
        
        if not content_str.strip():
            logger.error("File content is empty")
            return False
        
        # Detect file type
        file_type = _detect_file_type(file_content)
        logger.info(f"Detected file type: {file_type}")
        
        if file_type == 'json':
            # Validate JSON structure first
            if not _validate_json_file(file_content):
                logger.error("Invalid JSON file")
                return False
            
            # Convert JSON to YAML for processing
            yaml_content = _convert_json_to_yaml(file_content)
            if not yaml_content:
                logger.error("Failed to convert JSON to YAML")
                return False
            
            # Parse the converted YAML
            try:
                spec = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                logger.error(f"Invalid YAML after conversion: {e}")
                return False
                
        elif file_type == 'yaml':
            # Parse YAML directly
            try:
                spec = yaml.safe_load(content_str)
            except yaml.YAMLError as e:
                logger.error(f"Invalid YAML syntax: {e}")
                return False
        else:
            logger.error("File is neither valid JSON nor YAML")
            return False
        
        # Validate the parsed specification
        if not spec or not isinstance(spec, dict):
            logger.error("File does not contain valid object structure")
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

def validate_postman_collection(spec: dict) -> bool:
    """
    Validate Postman collection structure
    This is for when you want to accept Postman collections as input
    """
    try:
        logger.info("Validating Postman collection structure...")
        
        # Check for Postman collection required fields
        if 'info' not in spec:
            logger.error("Missing 'info' section in Postman collection")
            return False
            
        info = spec['info']
        if not isinstance(info, dict):
            logger.error("'info' section must be an object")
            return False
            
        # Check for Postman-specific fields
        if 'name' not in info:
            logger.error("Missing 'name' field in Postman collection info")
            return False
            
        # Check for items (requests)
        if 'item' not in spec:
            logger.error("Missing 'item' section (requests) in Postman collection")
            return False
            
        items = spec['item']
        if not isinstance(items, list):
            logger.error("'item' section must be an array")
            return False
            
        # Validate at least one item has request structure
        valid_items = 0
        for item in items:
            if isinstance(item, dict) and 'request' in item:
                request = item['request']
                if isinstance(request, dict) and 'method' in request and 'url' in request:
                    valid_items += 1
                    
        if valid_items == 0:
            logger.error("No valid requests found in Postman collection")
            return False
            
        logger.info(f"Postman collection validation passed - found {valid_items} valid requests")
        return True
        
    except Exception as e:
        logger.error(f"Postman collection validation error: {e}")
        return False