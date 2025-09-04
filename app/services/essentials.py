import os
from openai import OpenAI
from app.constants import OPENAI_API_KEY, MONGO_URI
import traceback
from pymongo import MongoClient

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set. Create a .env next to main.py or export it.")


client = OpenAI(api_key=OPENAI_API_KEY)
mongo_client = MongoClient(MONGO_URI) if MONGO_URI else None

try:
    # start example code here
    # end example code here
    client.admin.command("ping")
    print("Connected successfully")
    # other application code
    client.close()
except Exception as e:
    raise Exception(
        "The following error occurred: ", e)