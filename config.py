import os
from dotenv import load_dotenv
from google import genai

# Load .env file
load_dotenv()

# Read Secret Keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def check_keys():
    """Check whether required keys are available."""

    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN not found in .env")

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env")


def get_gemini_client():
    """Return Gemini Client"""
    return genai.Client(api_key=GEMINI_API_KEY)