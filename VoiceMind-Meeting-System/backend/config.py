"""
Configuration settings for VoiceMind Meeting System
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))

# Database Configuration (MySQL)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "voicemind_db")

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Audio Processing Configuration
SAMPLE_RATE = 16000
CHUNK_DURATION_MS = 10000  # 10 seconds
UPLOAD_FOLDER = "uploads/audio_chunks"
LOG_FOLDER = "logs"

# Whisper Model Configuration
WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large

# LLM Configuration
LLM_MODEL = "gpt-3.5-turbo"
LLM_TEMPERATURE = 0.7
MAX_TOKENS = 500

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
