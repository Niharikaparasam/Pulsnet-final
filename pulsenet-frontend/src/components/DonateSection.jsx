// src/components/DonateSection.jsx
import React, { useEffect, useState } from "react";
import { fetchMyDonorProfile, registerDonor } from "../api";

const DonateSection = () => {
  const [form, setForm] = useState({
    address: "",
    lat: "",
    lon: "",
    availability: "yes",
    last_donation_date: "",
    phone: "",
    notes: "",
  });
  const [status, setStatus] = useState("");
  const [loadedProfile, setLoadedProfile] = useState(false);

  useEffect(() => {
    // load existing donor profile if exists
    const loadProfile = async () => {
      try {
        const profile = await fetchMyDonorProfile();
        setForm({
          address: profile.address || "",
          lat: profile.lat ?? "",
          lon: profile.lon ?? "",
          availability: profile.availability || "yes",
          last_donation_date: profile.last_donation_date || "",
          phone: profile.phone || "",
          notes: profile.notes || "",
        });
        setStatus("Loaded your existing donor profile.");
      } catch (err) {
        // 404 means not registered yet
        if (err?.response?.status === 404) {
          setStatus("You are not yet registered as a donor. Fill the form to register.");
        } else {
          console.error(err);
          setStatus("Could not load donor profile.");
        }
      } finally {
        setLoadedProfile(true);
      }
    };

    loadProfile();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("Saving your donor profile...");

    try {
      const payload = {
        address: form.address || null,
        lat: form.lat ? Number(form.lat) : null,
        lon: form.lon ? Number(form.lon) : null,
        availability: form.availability,
        last_donation_date: form.last_donation_date || null,
        phone: form.phone || null,
        notes: form.notes || null,
      };

      const res = await registerDonor(payload);
      setStatus("Donor profile saved successfully.");
      // update from response (clean)
      setForm({
        address: res.address || "",
        lat: res.lat ?? "",
        lon: res.lon ?? "",
        availability: res.availability || "yes",
        last_donation_date: res.last_donation_date || "",
        phone: res.phone || "",
        notes: res.notes || "",
      });
    } catch (err) {
      console.error(err);
      const msg =
        err?.response?.data?.detail ||
        "Failed to save donor profile. Check backend.";
      setStatus(msg);
    }
  };

  return (
    <section className="section">
      <h2>Become a blood donor</h2>
      <p>
        Register yourself as a donor. Your details will be used by the matching
        engine when someone searches for compatible donors near your location.
      </p>

      {!loadedProfile && <p className="status">Loading your profile...</p>}

      <form className="form" onSubmit={handleSubmit}>
        <label>
          Address / Location
          <input
            name="address"
            placeholder="eg. Koramangala, Bengaluru"
            value={form.address}
            onChange={handleChange}
          />
        </label>

        <div className="two-col">
          <label>
            Latitude (optional)
            <input
              type="number"
              name="lat"
              step="0.000001"
              value={form.lat}
              onChange={handleChange}
            />
          </label>
          <label>
            Longitude (optional)
            <input
              type="number"
              name="lon"
              step="0.000001"
              value={form.lon}
              onChange={handleChange}
            />
          </label>
        </div>

        <div className="two-col">
          <label>
            Availability
            <select
              name="availability"
              value={form.availability}
              onChange={handleChange}
            >
              <option value="yes">Available</option>
              <option value="no">Not available</option>
              <option value="temporary_unavailable">Temporarily unavailable</option>
            </select>
          </label>

          <label>
            Last donation date (YYYY-MM-DD)
            <input
              name="last_donation_date"
              placeholder="2025-05-20"
              value={form.last_donation_date}
              onChange={handleChange}
            />
          </label>
        </div>

        <label>
          Phone (override if different from account phone)
          <input
            name="phone"
            value={form.phone}
            onChange={handleChange}
          />
        </label>

        <label>
          Notes (optional)
          <textarea
            name="notes"
            rows={3}
            value={form.notes}
            onChange={handleChange}
            style={{
              resize: "vertical",
              padding: "0.4rem 0.6rem",
              borderRadius: "0.5rem",
              border: "1px solid #374151",
              background: "#020617",
              color: "#e5e7eb",
            }}
          />
        </label>

        <button type="submit" className="btn primary">
          Save donor profile
        </button>
      </form>

      {status && <p className="status">{status}</p>}
    </section>
  );
};

export default DonateSection;
