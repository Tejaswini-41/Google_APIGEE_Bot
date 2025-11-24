# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CORS_ORIGINS = ["http://localhost:8080", "http://localhost:3000", "http://localhost:5000"]

# LLM Configuration
MODEL_NAME = "llama-3.3-70b-versatile"
MAX_TOKENS = 2048
TEMPERATURE_CREATIVE = 0.7
TEMPERATURE_PRECISE = 0.1

# Vector Store Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DB_PATH = "./chroma_db"
PROCESSED_DOCS_PATH = "./processed_docs/processed_docs.json"
MEMORY_WINDOW = 10

# Apigee Configuration - ENABLE REAL CREATION
DEVELOPMENT_MODE = False  # Set to False for real Apigee operations
APIGEE_BASE_URL = "https://apigee.googleapis.com/v1"

# Environment Variables for Apigee
APIGEE_ORG = os.getenv("APIGEE_ORG", "")
APIGEE_TOKEN = os.getenv("APIGEE_TOKEN", "")
APIGEE_ENVIRONMENT = os.getenv("APIGEE_ENVIRONMENT", "test")