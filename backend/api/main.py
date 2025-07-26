"""
Fast API : OpenAPI/Swagger specification validation and correction tool that integrates 
with Postman and uses Claude/GPT for intelligent corrections.

"""
import sys
import os 
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging

from config.logging import setup_logging
