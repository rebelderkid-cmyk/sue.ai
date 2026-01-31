import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";

// Explicitly using the values provided by the user to rule out ENV issues
const firebaseConfig = {
    apiKey: "AIzaSyDVdif4wW7fhDk6j4NiIULnSgth4TqpZrs",
    authDomain: "sue-ai.firebaseapp.com",
    projectId: "sue-ai",
    storageBucket: "sue-ai.firebasestorage.app",
    messagingSenderId: "439622404232",
    appId: "1:439622404232:web:4bbc9986628ca79b95773d",
    measurementId: "G-1WKMGK0KT2"
};

// Initialize Firebase (Singleton)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
export const auth = getAuth(app);
export default app;
