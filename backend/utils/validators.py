import sys
import os
import logging
from dotenv import load_dotenv
from config.logging import setup_logging

# Setup logging
setup_logging()


def validate_file(file) -> bool:
    try:
            
        valid_metadata = validate_metadata()
        if valid_metadata != True:
            return False # Or raise FileError
        
    except Exception as e:
        print("Could Not Validate File")
    


def validate_metadata(file) -> bool:
    pass

def validate_file_structure(file) -> bool:
    pass

