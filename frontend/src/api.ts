import axios from "axios";

// Determine base URLs based on window location or environment
// In local development, Vite proxies relative API calls to the backend. This
// avoids a separate browser origin (and therefore CORS preflight failures).
const API_URL = import.meta.env.VITE_API_URL || "";
export const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000`;

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Automatically inject JWT Token if present
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("bingo_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept 401 Unauthorized errors to automatically logout
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("bingo_token");
      localStorage.removeItem("bingo_user");
      // Do not redirect inside the interceptor to prevent loop issues; let the app handles it.
    }
    return Promise.reject(error);
  }
);

export default api;
