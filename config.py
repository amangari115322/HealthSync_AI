import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "HealthSync AI"
APP_VERSION = "1.0.0"

AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_API_URL = os.getenv("AI_API_URL", "")
AI_MODEL = os.getenv("AI_MODEL", "")

DATABASE_NAME = "healthsync.db"