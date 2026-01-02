import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found.")
    exit(1)

genai.configure(api_key=api_key)

models_to_test = [
    "models/gemini-3-pro",
    "models/gemini-3-flash-preview", 
    "gemini-3-pro",
    "gemini-3-flash-preview"
]

print("Testing Gemini 3 Models...")

for model_name in models_to_test:
    print(f"\n--- Testing: {model_name} ---")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, are you Gemini 3?")
        print(f"✅ SUCCESS! Response: {response.text}")
        break
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
