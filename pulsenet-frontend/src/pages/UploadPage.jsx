// src/pages/UploadPage.jsx
import React from "react";
import Navbar from "../components/Navbar";
import UploadSection from "../components/UploadSection";
import { useAuth } from "../AuthContext";

const UploadPage = () => {
  const { user } = useAuth();
  const isHospital = user?.role === "hospital";

  return (
    <>
      <Navbar />
      <main className="page">
        <section className="section">
          <h1>📤 Upload CSV Data</h1>
          <p>
            Upload donors, requests and hospital information as CSV files.
            This section is restricted to hospital admin accounts.
          </p>
        </section>

        {isHospital ? (
          <UploadSection />
        ) : (
          <p className="status">
            You are not allowed to access this page. Only hospital accounts can
            upload data.
          </p>
        )}
      </main>
    </>
  );
};

export default UploadPage;
