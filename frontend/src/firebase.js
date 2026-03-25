import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// TODO: Replace with your exact config from the Firebase Console (Step 4 of the Setup Guide)
const firebaseConfig = {
  apiKey: "AIzaSyBPd345-Nk8HzWLw8R0_f1-EnosYyHBpKY",
  authDomain: "predentes-cbb69.firebaseapp.com",
  projectId: "predentes-cbb69",
  storageBucket: "predentes-cbb69.firebasestorage.app",
  messagingSenderId: "787294829272",
  appId: "1:787294829272:web:49adbdd3d2526c38b8f5ad"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Auth and Firestore
export const auth = getAuth(app);
export const db = getFirestore(app);

export default app;
