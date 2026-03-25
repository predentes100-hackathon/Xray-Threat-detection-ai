import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyBrzRjTmnwggxElD_P-cP2rAql4W27LDXs"
genai.configure(api_key=GEMINI_API_KEY)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
