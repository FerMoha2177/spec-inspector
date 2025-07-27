"""
LLM Service with Claude using Messages API
"""
from config.logging import setup_logging
from dotenv import load_dotenv
import logging
import os
from anthropic import Anthropic

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.anthropic_client = None
        
        # Initialize Claude if API key available
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            try:
                self.anthropic_client = Anthropic(api_key=api_key)
                logger.info("Claude client initialized successfully")
                logger.info(f"Client has messages: {hasattr(self.anthropic_client, 'messages')}")
                
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self.anthropic_client = None
        else:
            logger.warning("No ANTHROPIC_API_KEY found - LLM service may not work")

    def calculate_max_tokens(self, input_content: str) -> int:
        """Calculate appropriate max tokens based on input size"""
        input_tokens = len(input_content) // 4  # Rough estimate: 4 chars = 1 token
        
        if input_tokens < 2000:
            return 4000   # Small API
        elif input_tokens < 10000:
            return 16000  # Medium API  
        elif input_tokens < 30000:
            return 32000  # Large API
        else:
            return 50000  # Enterprise API

    def get_corrections(self, file_content: bytes) -> dict:
        """
        Get both suggestions and corrected spec for the OpenAPI file.
        Returns dict with 'suggestions' and 'corrected_spec'
        """
        if not self.anthropic_client:
            return {
                "suggestions": "Error: No Claude API key configured or client initialization failed",
                "corrected_spec": ""
            }
            
        try:
            content_str = file_content.decode('utf-8')
            max_tokens = self.calculate_max_tokens(content_str)
            
            logger.info(f"Sending request to Claude with max_tokens: {max_tokens}")
            
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user", 
                        "content": (
                            "You are an OpenAPI 3.1.0 expert. Analyze and correct the following YAML specification.\n\n"
                            
                            "REQUIREMENTS:\n"
                            "- Fix all structural errors and validation issues\n"
                            "- Enhance metadata, schemas, tags, and security\n"
                            "- Return complete, valid OpenAPI 3.1.0 YAML\n"
                            "- Add helpful inline comments explaining fixes\n\n"
                            
                            "MUST INCLUDE:\n"
                            "- openapi: 3.1.0\n"
                            "- info.title, info.version, info.description\n"
                            "- info.termsOfService, info.contact, info.license\n"
                            "- servers (at least one)\n"
                            "- paths (can be empty object)\n"
                            "- components.schemas\n"
                            "- components.securitySchemes\n"
                            "- security (global)\n"
                            "- tags\n\n"
                            
                            "FORMATTING:\n"
                            "- Start with multi-line comment block explaining changes\n"
                            "- Add inline comments for fixes and improvements\n"
                            "- Use proper YAML structure (no duplicate keys)\n"
                            "- Include validation constraints where appropriate\n\n"
                            
                            "CRITICAL YAML RULES:\n"
                            "- NEVER use duplicate keys at the same level (e.g., two 'schemas:' in components)\n"
                            "- All schemas must be in ONE 'schemas:' section under components\n"
                            "- Put Error schema with other schemas, not separately\n"
                            "- Valid structure: components: { schemas: { User: ..., Error: ... }, responses: ..., securitySchemes: ... }\n\n"
                            
                            "Format your response as:\n"
                            "## SUGGESTIONS:\n"
                            "[Bulleted list of specific issues found and how they were fixed]\n\n"
                            "## CORRECTED SPEC:\n"
                            "```yaml\n"
                            "[Complete corrected YAML file]\n"
                            "```\n\n"
                            f"File to analyze:\n```yaml\n{content_str}\n```"
                        )
                    }
                ]
            )
            
            full_response = response.content[0].text
            logger.info("Successfully received response from Claude")
            
            # Parse the response to separate suggestions and corrected spec
            return self._parse_claude_response(full_response)
            
        except Exception as e:
            logger.error(f"Could not get corrections from Claude: {e}")
            return {
                "suggestions": f"Error: Could not analyze file - {str(e)}",
                "corrected_spec": ""
            }

    def _parse_claude_response(self, full_response: str) -> dict:
        """
        Parse Claude's response to extract suggestions and corrected spec
        """
        try:
            if "## SUGGESTIONS:" in full_response and "## CORRECTED SPEC:" in full_response:
                parts = full_response.split("## CORRECTED SPEC:")
                suggestions = parts[0].replace("## SUGGESTIONS:", "").strip()
                corrected_spec = parts[1].strip()
                
                # Extract YAML from code block if present
                if "```yaml" in corrected_spec:
                    yaml_start = corrected_spec.find("```yaml") + 7
                    yaml_end = corrected_spec.find("```", yaml_start)
                    if yaml_end != -1:
                        corrected_spec = corrected_spec[yaml_start:yaml_end].strip()
                    else:
                        corrected_spec = corrected_spec[yaml_start:].strip()
                        
                return {
                    "suggestions": suggestions,
                    "corrected_spec": corrected_spec
                }
            
            # Fallback if format not followed
            logger.warning("Claude response did not follow expected format")
            return {
                "suggestions": "AI response format error - manual review needed",
                "corrected_spec": full_response
            }
            
        except Exception as e:
            logger.error(f"Error parsing Claude response: {e}")
            return {
                "suggestions": f"Error parsing response: {str(e)}",
                "corrected_spec": full_response
            }

    def test_connection(self) -> dict:
        """
        Test the Claude connection with a simple request
        """
        if not self.anthropic_client:
            return {"success": False, "error": "No Claude client available"}
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                messages=[{"role": "user", "content": "Hello, please respond with 'Claude is working!'"}]
            )
            
            return {
                "success": True, 
                "response": response.content[0].text.strip(),
                "model": "claude-3-5-sonnet-20241022"
            }
            
        except Exception as e:
            logger.error(f"Claude connection test failed: {e}")
            return {"success": False, "error": str(e)}


    def get_service_info(self) -> dict:
        """
        Get information about the LLM service status
        """
        try:
            import importlib.metadata
            anthropic_version = importlib.metadata.version('anthropic')
        except Exception:
            anthropic_version = "Unknown"
        
        return {
            "service_name": "LLM Service",
            "claude_available": self.anthropic_client is not None,
            "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "anthropic_version": anthropic_version,
            "supported_models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
            "max_tokens_supported": 50000
        }