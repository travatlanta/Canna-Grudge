import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js";
import {
  getAuth, onAuthStateChanged, signInWithPopup,
  GoogleAuthProvider, FacebookAuthProvider, OAuthProvider, signOut
} from "https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js";

// Your Firebase project config
const firebaseConfig = {
  apiKey: "AIzaSyDfaW5SAZD_LlY7jsnLLNx4PaCYsm2gd7o",
  authDomain: "cannagrudgeauth.firebaseapp.com",
  projectId: "cannagrudgeauth",
  storageBucket: "cannagrudgeauth.firebasestorage.app",
  messagingSenderId: "628282357987",
  appId: "1:628282357987:web:d40180ce7e6255a0d6add6",
  measurementId: "G-NE07PR60GS"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
auth.useDeviceLanguage();

// Providers
const googleProvider = new GoogleAuthProvider();
const facebookProvider = new FacebookAuthProvider();
const appleProvider = new OAuthProvider('apple.com');

// Expose tiny API for other pages
window.__cgAuth = {
  auth,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
  googleProvider,
  facebookProvider,
  appleProvider
};
