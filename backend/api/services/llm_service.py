"""
LLM Service

This service is responsible for interacting with the LLM to get corrections for the OpenAPI 3.1 specification.
"""
from config.logging import setup_logging
from dotenv import load_dotenv
import logging
import os
import sys
from openai import OpenAI
import claude


load_dotenv()

setup_logging()
logger = logging.getLogger(__name__)

claude_client = claude.Client(api_key=os.getenv("CLAUDE_API_KEY"))

class LLMService:
    def __init__(self):
        self.client = claude.Client(api_key=os.getenv("CLAUDE_API_KEY"))
    

    def get_corrections(self, file_content: bytes) -> str:
        """
        Get corrections for the OpenAPI 3.1 specification.
        """
        try:
            response = self.client.chat.completions.create(
                model="claude-3-5-sonnet-20240620",
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Correct the following OpenAPI 3.1 specification file "
                            "to be valid OpenAPI 3.1. The file is a YAML file "
                            "encoded in UTF-8. Please include the full file content with corrections "
                            "in your response.\n\n" + file_content.decode('utf-8')
                        )
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Could not get corrections: {e}")
            return ""