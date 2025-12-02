// src/pages/MatchPage.jsx
import React from "react";
import Navbar from "../components/Navbar";
import UploadSection from "../components/UploadSection";
import MatchSection from "../components/MatchSection";
import { useAuth } from "../AuthContext";

const MatchPage = () => {
  const { user } = useAuth();
  const isHospital = user?.role === "hospital";

  return (
    <>
      <Navbar />
      <main className="page">
        <section className="section">
          <h1>🔍 Find Donor Match</h1>
          <p>
            Search nearby donors based on blood group compatibility and
            geo-distance. Hospitals can also upload bulk data.
          </p>
        </section>

        {/* Only hospitals can upload CSV */}
        {isHospital && <UploadSection />}

        <MatchSection />
      </main>
    </>
  );
};

export default MatchPage;
