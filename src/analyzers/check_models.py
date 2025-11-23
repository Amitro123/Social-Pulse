# check_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("🔍 Checking available Gemini models...\n")
available_models = []

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        available_models.append(model.name)

if not available_models:
    print("❌ No models available! Check your API key.")
else:
    print(f"\n📊 Total: {len(available_models)} models available")
    print(f"\n💡 Use this in your code: '{available_models[0]}'")
