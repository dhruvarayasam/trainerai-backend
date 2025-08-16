import os
from openai import OpenAI
from constants import OPENAI_API_KEY, DEBUG, MODEL, SYSTEM_PROMPT
import traceback

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set. Create a .env next to main.py or export it.")
client = OpenAI(api_key=OPENAI_API_KEY)
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set. Create a .env next to main.py or export it.")

def _log_exc(kind: str, e: Exception):
    # Print rich diagnostics to server logs, but keep responses generic
    print(f"[{kind}] {e.__class__.__name__}: {e}")
    for attr in ("status_code", "request_id"):
        if hasattr(e, attr):
            print(f"  {attr}: {getattr(e, attr)}")
    traceback.print_exc()

def _msg(public_msg: str):
    return {"message": f"{public_msg} Please try again later." if not DEBUG else public_msg}