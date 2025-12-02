// src/pages/DonatePage.jsx
import React from "react";
import Navbar from "../components/Navbar";
import DonateSection from "../components/DonateSection";

const DonatePage = () => {
  return (
    <>
      <Navbar />
      <main className="page">
        <section className="section">
          <h1>❤️ Donate Blood</h1>
          <p>
            Register yourself as a donor. Your details will be considered for
            future matching requests.
          </p>
        </section>

        <DonateSection />
      </main>
    </>
  );
};

export default DonatePage;
