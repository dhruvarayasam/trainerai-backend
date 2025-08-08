# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError, NotFoundError
import os
import traceback

HERE = Path(__file__).parent
load_dotenv(dotenv_path=HERE / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set. Create a .env next to main.py or export it.")

client = OpenAI(
    api_key=OPENAI_API_KEY
    
)

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str

SYSTEM_PROMPT = (
    "You are a certified nutritionist AI assistant. Provide helpful, accurate, and safe dietary advice. "
    "Only respond to questions related to food, diets, nutrition, or health goals like weight loss, "
    "muscle gain, and allergies. Politely refuse unrelated questions."
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # safer default in 2025; change if needed

@app.get("/health")
def health():
    # basic app health without calling OpenAI
    return {"ok": True}

@app.get("/debug/ping")
def ping():
    # quick sanity check that env is visible (never return secrets)
    return {
        "ok": True,
        "has_key": bool(OPENAI_API_KEY),
        "model": MODEL,
        "debug": DEBUG,
    }

@app.post("/ask")
def ask_bot(req: ChatRequest):
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt must not be empty.")

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return {"response": resp.choices[0].message.content}

    except AuthenticationError as e:
        _log_exc("AuthenticationError", e)
        return JSONResponse(status_code=401, content=_msg("Bad OpenAI credentials."))

    except NotFoundError as e:
        # e.g., model not found or not enabled for your account
        _log_exc("NotFoundError (likely model)", e)
        return JSONResponse(
            status_code=400,
            content=_msg(f"Model '{MODEL}' not available. Try a different model.")
        )

    except RateLimitError as e:
        _log_exc("RateLimitError", e)
        return JSONResponse(status_code=429, content=_msg("Rate limited. Please retry."))

    except APIConnectionError as e:
        _log_exc("APIConnectionError", e)
        return JSONResponse(status_code=503, content=_msg("Network/connectivity issue."))

    except APIError as e:
        _log_exc("APIError", e)
        return JSONResponse(status_code=502, content=_msg("OpenAI API error."))

    except Exception as e:
        _log_exc("UnexpectedError", e)
        return JSONResponse(status_code=500, content=_msg("Unexpected server error."))

def _log_exc(kind: str, e: Exception):
    # Print rich diagnostics to server logs, but keep responses generic
    print(f"[{kind}] {e.__class__.__name__}: {e}")
    for attr in ("status_code", "request_id"):
        if hasattr(e, attr):
            print(f"  {attr}: {getattr(e, attr)}")
    traceback.print_exc()

def _msg(public_msg: str):
    return {"message": f"{public_msg} Please try again later." if not DEBUG else public_msg}
