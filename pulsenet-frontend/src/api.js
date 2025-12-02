// src/api.js
import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("access_token");
}

export const apiClient = axios.create({
  baseURL: API_BASE,
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---- AUTH ----
export async function signup(user) {
  const res = await apiClient.post("/api/auth/signup", user);
  return res.data;
}

export async function login(email, password) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const res = await apiClient.post("/api/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data; // {access_token, token_type}
}

export async function fetchCurrentUser() {
  const res = await apiClient.get("/api/auth/me");
  return res.data;
}

// ---- UPLOAD CSV ----
export async function uploadCsv(endpoint, file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await apiClient.post(endpoint, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

// ---- MATCH ----
export async function fetchMatches(payload) {
  const res = await apiClient.post("/api/match", payload);
  return res.data;
}

// ---- DONATIONS ----
export async function fetchMyDonorProfile() {
  const res = await apiClient.get("/api/donations/me");
  return res.data;
}

export async function registerDonor(data) {
  const res = await apiClient.post("/api/donations/register", data);
  return res.data;
}
