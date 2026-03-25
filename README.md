# Shieldex AI Customs Dashboard

Shieldex is an AI-powered X-ray threat detection platform designed for customs and security analysts. It uses a YOLOv11 model trained on the PIDray dataset for real-time item detection and integrates Google's Gemini 2.0 Flash to provide expert security insights.

## System Architecture

- **Backend**: FastAPI, Ultralytics YOLOv11, Google Generative AI (Gemini), Firebase Admin.
- **Frontend**: React (Vite), Firebase Authentication, Cloud Firestore.

---

## ⚙️ Configuration & Variables

To run this project securely, you must declare and configure the following variables for both the backend and frontend.

### 1. Backend Configuration (`/backend`)

The backend requires the following configuration to handle AI inference and database operations.

#### A. Gemini API Key
The application queries Gemini 2.0 Flash for threat mitigation recommendations.
1. Create a `.env` file inside the `/backend` directory:
   ```env
   GEMINI_API_KEY="your_google_ai_studio_api_key_here"
   ```
2. Alternatively, set it as a system environment variable before running the Python server.

#### B. Firebase Admin SDK
Used for server-side verification and updating global scan logs.
1. Go to **Firebase Console** &rarr; **Project Settings** &rarr; **Service Accounts**.
2. Click **Generate new private key** and download the JSON file.
3. Rename the file to `serviceAccountKey.json`.
4. Place it directly inside the `/backend` directory. *(Note: This file is ignored by `.gitignore` to prevent secret leaks)*.

#### C. YOLO Model
By default, the backend will look for a custom trained model at `models/pidray_detector/weights/best.pt`. If it isn't found, it seamlessly falls back to the base `yolo11n.pt` model included in the repo.

### 2. Frontend Configuration (`/frontend`)

The frontend uses Firebase Client SDK for user authentication and client-side database reads.

Open `frontend/src/firebase.js` and update the `firebaseConfig` object with your project's credentials. Alternatively, you can migrate these to a `.env.local` file using Vite's `VITE_` prefix.

```javascript
// frontend/src/firebase.js
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.firebasestorage.app",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

---

## 🚀 Running the Application

### Running the Backend

Ensure you have Python 3.10+ installed.

```bash
cd backend
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate # On Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI Server
python -m uvicorn main:app --reload --port 8000
```
The backend will be available at `http://localhost:8000`.

### Running the Frontend

Ensure you have Node.js 18+ installed.

```bash
cd frontend
# Install dependencies
npm install

# Start the development server
npm run dev
```
The dashboard will be available at `http://localhost:5173`.