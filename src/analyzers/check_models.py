# check_models.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("🔍 Checking available Gemini models that support generateContent...\n")
models = [m for m in genai.list_models() if "generateContent" in getattr(m, "supported_generation_methods", [])]
for m in models:
    print(m.name)
