from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import google.generativeai as genai
import cv2
import numpy as np
import os
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

try:
    model = YOLO("models/pidray_detector/weights/best.pt")
except:
    print("Warning: Custom PIDray model not found, falling back to base YOLO11n.")
    model = YOLO("yolo11n.pt")


# 2. Configure Gemini 2.0 Flash
# IMPORTANT: Provide your actual Gemini API Key here or set it as an environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBrzRjTmnwggxElD_P-cP2rAql4W27LDXs")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

def get_gemini_recommendation(detected_items: str) -> str:
    """Queries Gemini 2.0 Flash for a customs security recommendation."""
    prompt = (
        f"Act as a customs expert and provide a 2-sentence security recommendation "
        f"based on these detected items in an X-ray scan: {detected_items}. "
        f"Be authoritative and concise."
    )
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.replace('\n', ' ').strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return f"Warning: Requires manual secondary inspection for {detected_items}."

@app.post("/api/scan")
async def process_scan(image: UploadFile = File(...)):
    # 3. Read the image sent from the React Dashboard
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 4. Use your trained YOLOv11 model to detect threats
    results = model(img)
    
    # 5. Extract insights and prompt Gemini
    if len(results) > 0 and len(results[0].boxes) > 0:
        # Get the detection with the highest confidence
        box = results[0].boxes[0]
        confidence = float(box.conf[0]) * 100
        class_id = int(box.cls[0])
        threat_class = model.names[class_id]
        
        # Call Gemini using the detected threat
        expert_insight = get_gemini_recommendation(threat_class)
        
        return {
            "threatType": f"Concealed Item ({threat_class})",
            "confidence": round(confidence, 1),
            "riskScore": int(confidence),
            "aiInsights": expert_insight
        }
    else:
        # Call Gemini for a clean scan
        expert_insight = get_gemini_recommendation("None (Clean Scan)")
        
        return {
            "threatType": "Clear",
            "confidence": 100,
            "riskScore": 0,
            "aiInsights": expert_insight
        }
