from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import io
import json
import PIL.Image
from firebase import init_firebase

app = FastAPI(title="Shieldex Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase
init_firebase()

# Configure Gemini 1.5 Flash (Vision + Text)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDh6HHSbseJIHgqerhQlBs66WyUsiCt390")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
print("[OK] Gemini 1.5 Flash model loaded.")


# ─────────────────────────────────────────────
# CORE: Gemini 1.5 Flash Vision X-ray Analysis
# ─────────────────────────────────────────────
def analyze_with_gemini_vision(image_bytes: bytes) -> dict | None:
    """
    Send the raw image to Gemini 1.5 Flash for X-ray threat analysis.
    Returns a structured dict or None if the API is unavailable.
    """
    try:
        pil_image = PIL.Image.open(io.BytesIO(image_bytes))

        prompt = """You are an expert customs security officer specializing in X-ray baggage scanning at border checkpoints.

This image is an X-RAY SCAN. X-ray images show objects as silhouettes with colour coding:
- Orange/dark = dense objects (metals, weapons)
- Blue/green = less dense objects (electronics, plastics)
- Black = very dense (e.g., gun barrels, thick metal)

Carefully analyze this X-ray scan for ANY threatening or prohibited items including:
- Firearms: pistols, revolvers, rifles, gun parts, gun barrels, magazines
- Bladed weapons: knives, box cutters, scissors, swords, razors
- Explosives: wires + battery combinations, pipe-like objects, detonators, suspect packages
- Drugs: compressed rectangular blocks, suspicious powders
- Other prohibited items: tasers, pepper spray canisters, restraints

IMPORTANT: Be AGGRESSIVE in threat detection. If you see ANY object that COULD be a weapon, flag it. 
X-ray shapes to watch for:
- Long thin dark shapes = gun barrel or knife blade
- L-shaped dark silhouette = pistol/handgun
- Cylindrical dense objects = pipe bomb or suppressor
- Rectangular brick shapes = drugs or explosives block

Respond ONLY with a valid JSON object — no markdown, no explanation, just raw JSON:
{
  "threat_detected": true or false,
  "threat_type": "exact name of the detected threat, or 'Clear' if nothing found",
  "confidence": integer from 0 to 100,
  "risk_score": integer from 0 to 100,
  "ai_insights": "2 authoritative sentences: first describe what you see in the X-ray, second give the action recommendation"
}

If you see a gun shape in this X-ray, threat_detected MUST be true. Be accurate and strict."""

        response = gemini_model.generate_content([prompt, pil_image])
        raw_text = response.text.strip()

        # Strip markdown code fences if Gemini wraps in ```json ... ```
        if "```" in raw_text:
            parts = raw_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                try:
                    return json.loads(part)
                except Exception:
                    continue

        return json.loads(raw_text)

    except Exception as e:
        print(f"⚠️  Gemini 1.5 Flash error: {e}")
        return None


# ─────────────────────────────────────────────
# API ENDPOINT
# ─────────────────────────────────────────────
@app.post("/api/scan")
async def process_scan(image: UploadFile = File(...)):
    contents = await image.read()

    # ── Gemini 1.5 Flash Vision Analysis ──────────────────────────
    gemini_result = analyze_with_gemini_vision(contents)

    if gemini_result:
        print(f"✅ Gemini 1.5 Flash result: {gemini_result}")
        threat_detected = gemini_result.get("threat_detected", False)
        threat_type     = gemini_result.get("threat_type", "Clear")
        confidence      = gemini_result.get("confidence", 100)
        risk_score      = gemini_result.get("risk_score", 0)
        ai_insights     = gemini_result.get("ai_insights", "No anomalies detected. Proceed with standard clearance.")

        # Normalise: if Gemini says not detected, force Clear
        if not threat_detected:
            threat_type = "Clear"
            risk_score  = min(risk_score, 5)

        return {
            "threatType": threat_type,
            "confidence": confidence,
            "riskScore":  risk_score,
            "aiInsights": ai_insights
        }

    # ── Gemini unavailable → static offline fallback ──────────────
    print("⚠️  Gemini 1.5 Flash unavailable. Returning offline fallback.")
    return {
        "threatType": "Scan Unavailable",
        "confidence": 0,
        "riskScore": 0,
        "aiInsights": "AI analysis service is temporarily offline. Manual inspection is required — do not clear this item automatically."
    }
