import os
from pathlib import Path
from dotenv import load_dotenv



HERE = Path(__file__).parent
load_dotenv(dotenv_path=HERE / ".env", override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

SYSTEM_PROMPT = (
    "You are a certified nutritionist and personal training AI assistant. Provide helpful, accurate, and safe dietary and fitness advice. "
    "Only respond to questions related to food, diets, nutrition, or health goals like weight loss, "
    "fitness, muscle gain, or general guidance on how to stay fit. Politely refuse unrelated questions."
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # safer default in 2025; change if needed
