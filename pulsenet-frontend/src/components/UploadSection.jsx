// src/components/UploadSection.jsx
import React, { useState } from "react";
import { uploadCsv } from "../api";

const UploadSection = () => {
  const [status, setStatus] = useState("");

  const handleUpload = async (endpoint, file) => {
    if (!file) return;
    try {
      setStatus("Uploading...");
      const res = await uploadCsv(endpoint, file);
      setStatus(
        `Upload to ${endpoint} ok. Rows: ${res.rows ?? "unknown"}`
      );
    } catch (err) {
      console.error(err);
      const msg =
        err?.response?.data?.detail || "Upload failed. See console.";
      setStatus(msg);
    }
  };

  return (
    <section className="section" id="upload">
      <h2>Upload CSV Data</h2>
      <p>Upload donors, hospitals and request CSVs used by the matching engine.</p>
      <div className="upload-grid">
        <UploadCard
          label="Donors"
          onUpload={(file) => handleUpload("/api/upload/donors", file)}
        />
        <UploadCard
          label="Hospitals"
          onUpload={(file) => handleUpload("/api/upload/hospitals", file)}
        />
        <UploadCard
          label="Requests"
          onUpload={(file) => handleUpload("/api/upload/requests", file)}
        />
      </div>
      {status && <p className="status">{status}</p>}
    </section>
  );
};

const UploadCard = ({ label, onUpload }) => {
  const [file, setFile] = useState(null);

  return (
    <div className="card upload-card">
      <h3>{label} CSV</h3>
      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files[0] || null)}
      />
      <button
        className="btn small"
        onClick={() => file && onUpload(file)}
        disabled={!file}
      >
        Upload
      </button>
    </div>
  );
};

export default UploadSection;
