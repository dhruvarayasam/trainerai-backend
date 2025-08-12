# main.py
from fastapi import FastAPI, HTTPException
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from pathlib import Path
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
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError, NotFoundError
import os
import traceback
import json
from typing import Dict, Any, List, Optional
from fastapi import Body
from pydantic import BaseModel, Field

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
    "You are a certified nutritionist and personal training AI assistant. Provide helpful, accurate, and safe dietary and fitness advice. "
    "Only respond to questions related to food, diets, nutrition, or health goals like weight loss, "
    "fitness, muscle gain, or general guidance on how to stay fit. Politely refuse unrelated questions."
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
class PlanSpecifications(BaseModel):
    num_days_a_week: int = Field(..., gt=0, description="Number of workout days per week")
    fitness_goal: str = Field(..., description="User's fitness goal (e.g., weight loss, muscle gain)")
    avg_workout_length: int = Field(..., gt=0, description="Average workout length in minutes")
    experience_level: str = Field(..., description="User's experience level (e.g., beginner, intermediate, advanced)")
    intensity: str = Field(..., description="Desired workout intensity (e.g., low, medium, high)")

class WorkoutExercise(BaseModel):
    exercise: str
    sets: int
    reps: int
    rest: Optional[str] = None

class WorkoutPlan(BaseModel):
    days: Dict[str, List[WorkoutExercise]]  # e.g., {"Monday": [WorkoutExercise, ...], ...}

class WorkoutPlanRequest(BaseModel):
    plan_specifications: PlanSpecifications

class WorkoutPlanResponse(BaseModel):
    workout_plan: WorkoutPlan

@app.post('/workout_plan', response_model=WorkoutPlanResponse)
async def generate_workout_plan(req: WorkoutPlanRequest = Body(...)):
    """
    Takes in request body which should contain 'plan_specifications' as a JSON object.
    Validates the plan_specifications and if valid, plugs into OpenAI API to generate a workout plan.
    Returns the generated workout plan or an error message if validation fails.
    Workout plan is also generated according to a specific schema --> error out if it doesn't follow this schema.
    RETURNS:
    json with 'workout_plan' key containing json of plan details
    400 Bad Request if 'plan_specifications' is missing or invalid, or if generation fails.
    """

    plan_specifications = req.plan_specifications

    user_prompt = (
        f"Generate a detailed workout plan according to the following specifications:\n"
        f"- Number of days per week: {plan_specifications.num_days_a_week}\n"
        f"- Fitness goal: {plan_specifications.fitness_goal}\n"
        f"- Average workout length (minutes): {plan_specifications.avg_workout_length}\n"
        f"- Experience level: {plan_specifications.experience_level}\n"
        f"- Intensity: {plan_specifications.intensity}\n"
        f"Return the plan as a JSON object with a 'days' key, where each key is a day of the week and the value is a list of exercises. Each exercise should have: exercise (str), sets (int), reps (int), and rest (str, optional). For any numeric values, only include the numbers, no units or extra text."
        f"For any numeric values that indicate time, assume that the unit is minutes unless otherwise specified. For example, if the user specifies 30 minutes, just return 30 without 'minutes'."
        f"Do not include any additional text or explanations, just the JSON object, and don't include the json signifier in the response, JUST the object."
    )   

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        content = resp.choices[0].message.content
        try:
            workout_plan_dict = json.loads(content)
            # Validate against WorkoutPlan schema
            workout_plan = WorkoutPlan(**workout_plan_dict)
        except Exception:
            raise HTTPException(status_code=502, detail="OpenAI did not return a valid JSON workout plan. Response was: " + content)

        return {"workout_plan": workout_plan}

    except Exception as e:
        _log_exc("UnexpectedError", e)
        return JSONResponse(status_code=500, content=_msg("Unexpected server error: " + str(e)))

    



@app.post("/ask")
def ask_bot(req: ChatRequest):
    """
TODO
instead of taking a generic prompt as input, enforce a JSON schema, extract information from JSON
and provide as prompt here
generate output according to a specific schema and return along with status code"""

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
