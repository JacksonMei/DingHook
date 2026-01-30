import os

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
SECRET = os.getenv("SECRET")

# Gemini (user provided API key + url)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL")  # e.g. https://api.example.com/v1/gemini

# Database (sqlite file path)
DATABASE_PATH = os.getenv("DATABASE_PATH", "dingbot_memory.db")

# Scheduler check interval in seconds
# Default to 60s per user request (can be overridden via env)
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))

# Model name to pass to the Gemini endpoint (if needed)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")

