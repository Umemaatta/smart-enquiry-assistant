import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API key not found!")
else:
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-3.6-flash")

    response = model.generate_content(
        "Explain what a university admission test is in one simple sentence."
    )

    print("\nGemini Response:")
    print(response.text)