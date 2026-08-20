import { initializeApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyDLppUdeGbuYK5oM82bSTo-6DwYQEWkz1k",
  authDomain: "web-bingo-6dcbe.firebaseapp.com",
  projectId: "web-bingo-6dcbe",
  storageBucket: "web-bingo-6dcbe.firebasestorage.app",
  messagingSenderId: "54125117099",
  appId: "1:54125117099:web:08fb9ffbd2993f676601ee",
  measurementId: "G-1DN22WFLXS",
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

isSupported().then((supported) => {
  if (supported) {
    getAnalytics(app);
  }
});
