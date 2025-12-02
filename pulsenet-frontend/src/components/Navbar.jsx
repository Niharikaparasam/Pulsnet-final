// src/components/Navbar.jsx
import React from "react";
import { useAuth } from "../AuthContext";
import { NavLink, useNavigate } from "react-router-dom";

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <div className="logo" onClick={() => navigate("/dashboard")}>
        PulseNet
      </div>
      <div className="nav-links">
        <NavLink to="/dashboard" end>
          Overview
        </NavLink>
        <NavLink to="/dashboard/match">Search Match</NavLink>
        <NavLink to="/dashboard/donate">Donate</NavLink>
      </div>
      <div className="nav-right">
        {user && (
           <span className="user-chip">
              {user.full_name || user.email} ({user.role})
           </span>
        )}

        <button className="btn small" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
