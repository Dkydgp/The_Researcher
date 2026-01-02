import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    found = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"AVAILABLE: {m.name}")
            found = True
    if not found:
        print("No generateContent models found.")
except Exception as e:
    print(f"Error: {e}")
