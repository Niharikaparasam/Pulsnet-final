// src/pages/Dashboard.jsx
import React from "react";
import { useAuth } from "../AuthContext";
import { Link } from "react-router-dom";
import "./dashboard.css";  // <-- Important

export default function Dashboard() {
  const { user } = useAuth();
  const isHospital = user?.role === "hospital";

  return (
    <div className="dashboard-container">

      {/* ---------------- HEADER ---------------- */}
      <header className="dash-header">
        <h1>🔥 PulseNet Dashboard</h1>
        <p>Smart Blood Donation Network • Realtime Matching • Geo-based Results</p>
      </header>

      {/* ---------------- USER BADGE ---------------- */}
      <div className="user-info">
        <span>Welcome, <strong>{user.full_name || user.email}</strong></span>
        <span className={`role-badge ${isHospital ? "hospital" : "user"}`}>
          {isHospital ? "🏥 Hospital Admin" : "🩸 Donor/User"}
        </span>
      </div>


      {/* ---------------- CARD SECTIONS ---------------- */}
      <div className="card-grid">

        {/* CARD 1 → MATCH */}
        <Link to="/dashboard/match" className="dash-card match">
          <h2>🔍 Find Donor Match</h2>
          <p>Search nearby donors using blood compatibility & distance AI.</p>
          <button>Find Match →</button>
        </Link>

        {/* CARD 2 → DONATE */}
        <Link to="/dashboard/donate" className="dash-card donate">
          <h2>❤️ Donate Blood</h2>
          <p>Register yourself as an active donor & save lives.</p>
          <button>Become Donor →</button>
        </Link>

        {/* CARD 3 → UPLOAD (Visible only for hospitals) */}
        {isHospital && (
          <Link to="/dashboard/upload" className="dash-card upload">
            <h2>📤 Upload CSV Data</h2>
            <p>Upload donor, request & hospital datasets (Admin Only)</p>
            <button>Upload Now →</button>
          </Link>
        )}

      </div>

    </div>
  );
}
