// src/pages/LoginPage.jsx
import React, { useState } from "react";
import { useAuth } from "../AuthContext";
import { useNavigate, Link, useLocation } from "react-router-dom";

const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("Logging in...");
    try {
      await login(email, password);
      setStatus("Login successful.");
      navigate(from, { replace: true });
    } catch (err) {
      console.error(err);
      const msg =
        err?.response?.data?.detail || "Login failed. Check credentials.";
      setStatus(msg);
    }
  };

  return (
    <div className="page center">
      <div className="card auth-card">
        <h1>PulseNet Login</h1>
        <form onSubmit={handleSubmit} className="form">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <button type="submit" className="btn primary">
            Login
          </button>
        </form>
        {status && <p className="status">{status}</p>}
        <p className="small">
          New user? <Link to="/signup">Create an account</Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
