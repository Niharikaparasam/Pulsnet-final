// src/App.js
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import Dashboard from "./pages/Dashboard";
import MatchPage from "./pages/MatchPage";
import DonatePage from "./pages/DonatePage";
import UploadPage from "./pages/UploadPage";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      {/* Dashboard home (cards) */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* Match page */}
      <Route
        path="/dashboard/match"
        element={
          <ProtectedRoute>
            <MatchPage />
          </ProtectedRoute>
        }
      />

      {/* Donate page */}
      <Route
        path="/dashboard/donate"
        element={
          <ProtectedRoute>
            <DonatePage />
          </ProtectedRoute>
        }
      />

      {/* Upload page (hospital only, we’ll handle inside) */}
      <Route
        path="/dashboard/upload"
        element={
          <ProtectedRoute>
            <UploadPage />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<div style={{ padding: "2rem" }}>Not found</div>} />
    </Routes>
  );
}

export default App;
