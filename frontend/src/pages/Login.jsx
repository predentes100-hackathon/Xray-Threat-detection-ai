import React, { useState } from 'react';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { auth } from '../firebase';
import './Login.css';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      if (isLogin) {
        await signInWithEmailAndPassword(auth, email, password);
      } else {
        await createUserWithEmailAndPassword(auth, email, password);
      }
    } catch (err) {
      if (err.code === 'auth/invalid-credential' || err.code === 'auth/user-not-found') {
        setError('ERR: CREDENTIALS_INVALID');
      } else if (err.code === 'auth/email-already-in-use') {
        setError('ERR: ID_ALREADY_REGISTERED');
      } else if (err.code === 'auth/weak-password') {
        setError('ERR: PASSCODE_STRENGTH_WEAK');
      } else {
        setError(`ERR: ${err.message.toUpperCase()}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
           <h2>SHIELDEX // <span>NEXUS</span></h2>
           <p className="login-subtitle">
            {isLogin ? 'RESTRICTED ACCESS // DEPT. OF BORDER SECURITY' : 'AUTHORIZATION REQUIRED // NEW ANALYST REGISTRATION'}
           </p>
        </div>

        {error && <div className="error-alert">{error}</div>}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label>Analyst ID (Email)</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
              disabled={loading}
              placeholder="OPERATIVE@SHIELDEX.GOV"
            />
          </div>
          <div className="input-group">
            <label>Secure Passcode</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required 
              disabled={loading}
              placeholder="••••••••••••"
            />
          </div>
          
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? 'VERIFYING CREDENTIALS...' : (isLogin ? 'INITIALIZE SECURE LINK' : 'REQUEST CLEARANCE')}
          </button>
        </form>

        <div className="login-footer">
          <button type="button" className="toggle-mode-btn" onClick={() => setIsLogin(!isLogin)} disabled={loading}>
            {isLogin ? '> REQUEST NEW ANALYST CLEARANCE' : '> RETURN TO SECURE SIGN IN'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
