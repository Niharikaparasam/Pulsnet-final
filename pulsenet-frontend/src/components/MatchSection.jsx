// src/components/MatchSection.jsx
import React, { useState } from "react";
import { fetchMatches } from "../api";
import MatchesTable from "./MatchesTable";
import { useVoice } from "../hooks/useVoice";
import MatchMap from "./MatchMap";

const bloodGroups = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"];

const MatchSection = () => {
  const [form, setForm] = useState({
    required_blood_group: "O+",
    address: "",
    lat: "",
    lon: "",
    units_needed: 1,
    urgency_level: "high",
    top_n: 5,
  });

  const [matches, setMatches] = useState([]);
  const [status, setStatus] = useState("");
  const [alert, setAlert] = useState(null);
  const [origin, setOrigin] = useState(null); // 👈 used by map

  const voiceText =
    alert?.message ||
    (matches.length
      ? `Found ${matches.length} matching donors. Nearest donor is ${
          matches[0].name
        }.`
      : status);

  useVoice(voiceText, [alert, matches, status]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]:
        name === "units_needed" || name === "top_n" ? Number(value) : value,
    }));
  };

  // 👇 NEW: Use browser geolocation for blue marker + form lat/lon
  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setStatus("Geolocation is not supported by this browser.");
      return;
    }

    setStatus("Detecting your location...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setForm((prev) => ({
          ...prev,
          lat: latitude.toFixed(6),
          lon: longitude.toFixed(6),
        }));
        setOrigin({ lat: latitude, lon: longitude });
        setStatus("Using your current location for search.");
      },
      (err) => {
        console.error(err);
        setStatus("Unable to get location: " + err.message);
      }
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setAlert(null);
    setStatus("Searching...");
    setMatches([]);

    try {
      const payload = {
        required_blood_group: form.required_blood_group,
        address: form.address || undefined,
        lat: form.lat ? Number(form.lat) : undefined,
        lon: form.lon ? Number(form.lon) : undefined,
        units_needed: form.units_needed,
        urgency_level: form.urgency_level,
        top_n: form.top_n,
      };

      // set origin for map (blue pin)
      if (payload.lat && payload.lon) {
        setOrigin({ lat: payload.lat, lon: payload.lon });
      } else {
        setOrigin(null);
      }

      const res = await fetchMatches(payload);
      setMatches(res.matches || []);
      setAlert(res.alert || null);

      if (!res.matches || !res.matches.length) {
        setStatus("No donors found for this request.");
      } else {
        setStatus("Matches loaded.");
      }
    } catch (err) {
      console.error(err);
      const msg =
        err?.response?.data?.detail ||
        "Error fetching matches. Check backend.";
      setStatus(msg);
    }
  };

  const alertClass =
    alert?.level === "critical"
      ? "alert alert-critical"
      : "alert alert-info";

  return (
    <section className="section" id="match">
      <h2>Search for matching donors</h2>
      <p>Provide blood group and location. You can use your current GPS location.</p>

      {alert && (
        <div className={alertClass}>
          <strong>
            {alert.type === "no_match"
              ? "No donors found"
              : "Critical match found"}
          </strong>
          <p style={{ whiteSpace: "pre-line" }}>{alert.message}</p>
        </div>
      )}

      <form className="form match-form" onSubmit={handleSubmit}>
        <div className="two-col">
          <label>
            Blood group
            <select
              name="required_blood_group"
              value={form.required_blood_group}
              onChange={handleChange}
            >
              {bloodGroups.map((bg) => (
                <option key={bg} value={bg}>
                  {bg}
                </option>
              ))}
            </select>
          </label>

          <label>
            Urgency
            <select
              name="urgency_level"
              value={form.urgency_level}
              onChange={handleChange}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </label>
        </div>

        <label>
          Location (address)
          <input
            name="address"
            placeholder="eg. Manipal Hospital, Bengaluru"
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

        {/* NEW button to fill lat/lon automatically */}
        <button
          type="button"
          className="btn small"
          style={{ marginTop: "0.4rem", width: "fit-content" }}
          onClick={handleUseMyLocation}
        >
          Use my current location
        </button>

        <div className="two-col">
          <label>
            Units needed
            <input
              type="number"
              name="units_needed"
              min={1}
              value={form.units_needed}
              onChange={handleChange}
            />
          </label>
          <label>
            Top N donors
            <input
              type="number"
              name="top_n"
              min={1}
              max={50}
              value={form.top_n}
              onChange={handleChange}
            />
          </label>
        </div>

        <button type="submit" className="btn primary">
          Find donors
        </button>
      </form>

      {status && <p className="status">{status}</p>}

      <MatchesTable matches={matches} />

      {/* Map with blue + red markers */}
      <MatchMap origin={origin} matches={matches} />
    </section>
  );
};

export default MatchSection;
