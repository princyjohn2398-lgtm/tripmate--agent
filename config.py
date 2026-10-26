import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
# Optional: set to use an OpenAI-compatible provider such as Groq.
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip() or None
