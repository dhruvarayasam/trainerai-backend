from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str

SYSTEM_PROMPT = """
You are a certified nutritionist AI assistant. Your job is to provide helpful, accurate, and safe dietary advice to users.
Only respond to questions related to food, diets, nutrition, or health goals like weight loss, muscle gain, and allergies.
Never answer unrelated questions (math, politics, programming, etc.).
"""

WORKOUT_PLAN_PROMPT = """You are a certified fitness trainer AI assistant. Your job is to provide helpful, accurate, and safe workout plans to users.
Only respond to questions related to exercise, fitness, or health goals like weight loss, muscle gain, and injuries.
Never answer unrelated questions (math, politics, programming, etc.). Here are the user's specific requirements:


"""

@app.post("/generate_diet_plan")
def ask_bot(req: ChatRequest):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.body.prompt}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return {"response": response["choices"][0]["message"]["content"]}
#http://127.0.0.1:8000/docs

@app.post('generate_workout_plan')
def generate_workout_plan(req: ChatRequest):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": WORKOUT_PLAN_PROMPT + req.body.prompt}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return {"response": response["choices"][0]["message"]["content"]}