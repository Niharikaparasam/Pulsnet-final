// src/pages/SignupPage.jsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signup } from "../api";

const SignupPage = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    phone: "",
    blood_group: "",
    role: "user",  
  });
  const [status, setStatus] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("Creating account...");
    try {
      await signup(form);
      setStatus("Signup successful. Redirecting to login...");
      setTimeout(() => navigate("/login"), 800);
    } catch (err) {
      console.error(err);
      const msg =
        err?.response?.data?.detail || "Signup failed. Try different email.";
      setStatus(msg);
    }
  };

  return (
    <div className="page center">
      <div className="card auth-card">
        <h1>Create PulseNet Account</h1>
        <form onSubmit={handleSubmit} className="form">
          <label>
            Full Name
            <input
              name="full_name"
              value={form.full_name}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Email
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Phone
            <input
              name="phone"
              value={form.phone}
              onChange={handleChange}
            />
          </label>
          <label>
            Account type
            <select
                name="role"
                value={form.role}
                onChange={handleChange}
            >
                <option value="user">Normal User</option>
                <option value="hospital">Hospital</option>
            </select>
           </label>

          <label>
            Blood Group (optional)
            <input
              name="blood_group"
              value={form.blood_group}
              onChange={handleChange}
              placeholder="O+"
            />
          </label>
          <button type="submit" className="btn primary">
            Sign Up
          </button>
        </form>
        {status && <p className="status">{status}</p>}
        <p className="small">
          Already registered? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
};

export default SignupPage;
