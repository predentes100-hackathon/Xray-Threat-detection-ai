import google.generativeai as genai
import os

GEMINI_API_KEY = "AIzaSyDh6HHSbseJIHgqerhQlBs66WyUsiCt390"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

try:
    response = model.generate_content("Hello, are you functional?")
    print(f"STATUS: SUCCESS")
    print(f"RESPONSE: {response.text}")
except Exception as e:
    print(f"STATUS: FAILURE")
    print(f"ERROR: {e}")
