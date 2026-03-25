import React, { useState, useRef } from 'react';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { signOut } from 'firebase/auth';
import { db, auth } from '../firebase';
import '../App.css';

function Dashboard({ user }) {
  const [scanStatus, setScanStatus] = useState('idle'); // idle, scanning, analyzing, complete, error
  const [selectedImage, setSelectedImage] = useState(null); // base64 preview
  const [imageFile, setImageFile] = useState(null); // actual file for API
  const [results, setResults] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImageFile(file);
      
      const reader = new FileReader();
      reader.onload = (loadEvent) => {
        setSelectedImage(loadEvent.target.result);
        setScanStatus('idle');
        setResults(null);
      };
      reader.readAsDataURL(file); // Stores image as base64 encoded data URI
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setImageFile(file);
      
      const reader = new FileReader();
      reader.onload = (loadEvent) => {
        setSelectedImage(loadEvent.target.result);
        setScanStatus('idle');
        setResults(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const saveToFirestore = async (scanData, imageUri) => {
    try {
      // NOTE: In production, upload the raw file to Firebase Storage to get a tiny URL.
      // For this demo, we'll store the base64 URI directly into Firestore to keep it simple.
      await addDoc(collection(db, "scans"), {
         image_url: imageUri.substring(0, 100) + "...[TRUNCATED_FOR_FIRESTORE]", // Truncated to avoid huge firestore docs in test
         detected_items: [scanData.threatType],
         risk_score: scanData.riskScore,
         confidence: scanData.confidence,
         timestamp: serverTimestamp(),
         user_uid: user?.uid,
         user_email: user?.email
      });
      console.log("Successfully logged scan to Firestore.");
    } catch (err) {
      console.error("Firebase Firestore Error: Could not save scan document.", err);
    }
  };

  const handleScan = async () => {
    if (!imageFile || !selectedImage) return;
    
    setScanStatus('scanning');
    
    try {
      // 1. Prepare file for FastAPI backend
      const formData = new FormData();
      formData.append('image', imageFile);

      // 2. Send actual image to your local YOLOv11 + Gemini Python API
      const response = await fetch('http://localhost:8000/api/scan', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Backend server error');
      }

      setScanStatus('analyzing');
      const data = await response.json();
      
      // 3. Update dashboard with real AI results
      setResults({
        riskScore: data.riskScore,
        confidence: data.confidence,
        threatType: data.threatType,
        aiInsights: data.aiInsights
      });
      
      setScanStatus('complete');
      
      // 4. Securely log this exact threat detection event to Firebase
      saveToFirestore(data, selectedImage);

    } catch (error) {
      console.error("Error during scan:", error);
      setScanStatus('error');
    }
  };

  const resetDashboard = () => {
    setSelectedImage(null);
    setImageFile(null);
    setResults(null);
    setScanStatus('idle');
  };

  const handleSignOut = () => {
    signOut(auth).catch((err) => console.error("Error signing out:", err));
  };

  return (
    <div className="dashboard-container">
      {/* Navigation */}
      <nav className="glass-nav">
        <div className="logo-container">
          <div className="logo-icon"></div>
          <h1>Shieldex <span>Intelligence</span></h1>
        </div>
        <div className="user-profile" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{user?.email}</span>
          <button onClick={handleSignOut} className="btn-secondary" style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}>
            Logout
          </button>
        </div>
      </nav>

      <main className="dashboard-main dashboard-grid">
        {/* Left Column: Analysis Zone */}
        <section className="analysis-zone">
          <header className="page-header">
            <h2>Customs Inspection</h2>
            <p>Upload X-ray scans for real-time AI threat detection and analysis.</p>
          </header>

          <div 
            className={`upload-zone glass-card ${selectedImage ? 'has-image' : ''}`}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => !selectedImage && fileInputRef.current.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept="image/*" 
              style={{ display: 'none' }} 
            />
            
            {!selectedImage ? (
              <div className="upload-placeholder">
                <div className="upload-icon">📁</div>
                <h3>Drag & Drop X-ray Image</h3>
                <p>or click to browse files</p>
                <span className="supported-formats">Supports JPG, PNG, TIFF, DICOM</span>
              </div>
            ) : (
              <div className="image-preview-container">
                <img src={selectedImage} alt="X-ray scan preview" className="preview-image" />
                {scanStatus === 'scanning' && <div className="scan-line"></div>}
                {scanStatus === 'complete' && <div className="bounding-box-demo"></div>}
              </div>
            )}
          </div>

          <div className="action-bar glass-card">
            <button 
              className={`btn-secondary ${!selectedImage ? 'disabled' : ''}`}
              onClick={resetDashboard}
              disabled={!selectedImage || scanStatus === 'scanning' || scanStatus === 'analyzing'}
            >
              Clear Image
            </button>
            <button 
              className={`scan-button ${scanStatus}`}
              onClick={handleScan}
              disabled={!selectedImage || scanStatus === 'scanning' || scanStatus === 'analyzing'}
            >
              {scanStatus === 'idle' && 'Run Threat Analysis'}
              {scanStatus === 'scanning' && 'Scanning Object...'}
              {scanStatus === 'analyzing' && 'Generating Insights...'}
              {scanStatus === 'complete' && 'Re-Scan Image'}
              {scanStatus === 'error' && 'Analysis Failed'}
            </button>
          </div>
        </section>

        {/* Right Column: Intelligence Sidebar */}
        <aside className="intelligence-sidebar">
          <div className="results-panel glass-card">
            <h3>Intelligence Report</h3>
            
            {!results && scanStatus === 'idle' && (
              <div className="empty-state">
                <div className="empty-icon">🛡️</div>
                <p>Upload an image and run analysis to view risk scores and AI insights.</p>
              </div>
            )}
            
            {(scanStatus === 'scanning' || scanStatus === 'analyzing') && (
              <div className="loading-state">
                <div className="spinner"></div>
                <p>{scanStatus === 'scanning' ? 'Running YOLOv11 detector...' : 'Querying Gemini AI...'}</p>
              </div>
            )}

            {results && scanStatus === 'complete' && (
              <div className="report-content fade-in">
                {/* Threat Type */}
                <div className="threat-banner critical">
                  <span className="status-dot"></span>
                  <strong>{results.threatType}</strong>
                </div>

                {/* Metrics */}
                <div className="metrics-container">
                  <div className="metric-box">
                    <span className="metric-label">Risk Score</span>
                    <div className="score-ring high-risk">
                      <span className="score-value">{results.riskScore}</span>
                      <span className="score-max">/100</span>
                    </div>
                  </div>
                  <div className="metric-box">
                    <span className="metric-label">Confidence</span>
                    <div className="confidence-bar-container">
                      <div className="confidence-bar" style={{width: `${results.confidence}%`}}></div>
                    </div>
                    <span className="confidence-value">{results.confidence}%</span>
                  </div>
                </div>

                {/* Gemini Insights */}
                <div className="gemini-insights">
                  <div className="gemini-header">
                    <h4>✨ AI Insights</h4>
                    <span className="badge">Gemini Advanced</span>
                  </div>
                  <div className="insight-text">
                    <p>{results.aiInsights}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </aside>
      </main>
    </div>
  );
}

export default Dashboard;
