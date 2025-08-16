# main.py
from fastapi import FastAPI, HTTPException
# main.py
from fastapi.responses import JSONResponse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError, NotFoundError
import os
import traceback
from routes import generate_plans
from constants import OPENAI_API_KEY, DEBUG, MODEL, SYSTEM_PROMPT
from pydantic import BaseModel

class ChatRequest(BaseModel):
    prompt: str




app = FastAPI()

"""
INCLUDE ROUTERS HERE
"""
app.include_router(generate_plans.router)






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



def _log_exc(kind: str, e: Exception):
    # Print rich diagnostics to server logs, but keep responses generic
    print(f"[{kind}] {e.__class__.__name__}: {e}")
    for attr in ("status_code", "request_id"):
        if hasattr(e, attr):
            print(f"  {attr}: {getattr(e, attr)}")
    traceback.print_exc()

def _msg(public_msg: str):
    return {"message": f"{public_msg} Please try again later." if not DEBUG else public_msg}
