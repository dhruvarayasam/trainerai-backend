from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
import json

from app.models.workout_plan_models import WorkoutPlanRequest, WorkoutPlan, WorkoutPlanResponse
from app.models.diet_plan_models import DietPlanRequest, DietPlan, DietPlanResponse
from app.services.essentials import client, _log_exc, _msg
from app.constants import MODEL, SYSTEM_PROMPT
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from openai import AuthenticationError, NotFoundError, RateLimitError, APIConnectionError, APIError




router = APIRouter(prefix="/generate_plan", tags=["Plan Generation"])



@router.post('/workout', response_model=WorkoutPlanResponse)
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
        f"Return the plan as a JSON object with a 'days' key, where each key is a day of the week and the value is a list of exercises. Each exercise should have: exercise (str), sets (int), reps (int), and rest (int). For any numeric values, only include the numbers, no units or extra text."
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

@router.post("/diet", response_model=DietPlanResponse)
async def generate_diet_plan(req: DietPlanRequest = Body(...)):
    specs = req.plan_specifications
    user_prompt = (
        "Generate a 7-day diet plan based on the following specifications:\n"
        f"- Target daily calories: {specs.calories_per_day}\n"
        f"- Dietary preference: {specs.dietary_preference}\n"
        f"- Meals per day: {specs.meals_per_day}\n"
        f"- Allergies/restrictions: {', '.join(specs.allergies) if specs.allergies else 'None'}\n"
        f"- Goal: {specs.goal}\n"
        "Return ONLY a JSON object with a top-level key 'days'. "
        "Each key under 'days' must be a day of the week, and the value is a list of meals. "
        "Each meal object must have: name (str), foods (List[str]), calories (int). "
        "All calorie values must be integers with no units. "
        "Ensure the daily total calories are approximately the target (+/- 10%). "
        "No extra text, no code fences—just the JSON object."
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
            diet_plan_dict = json.loads(content)
            diet_plan = DietPlan(**diet_plan_dict)  # pydantic validation
        except Exception:
            raise HTTPException(
                status_code=502,
                detail="OpenAI did not return a valid JSON diet plan. Response was: " + content,
            )

        return {"diet_plan": diet_plan}
    except AuthenticationError as e:
        _log_exc("AuthenticationError", e)
        return JSONResponse(status_code=401, content=_msg("Bad OpenAI credentials."))
    except NotFoundError as e:
        _log_exc("NotFoundError (likely model)", e)
        return JSONResponse(
            status_code=400,
            content=_msg(f"Model '{MODEL}' not available. Try a different model."),
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
