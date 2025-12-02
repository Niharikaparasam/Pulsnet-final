// src/components/MatchMap.jsx
import React, { useState, useMemo, useEffect, useCallback } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline } from "react-leaflet";
import L from "leaflet";
import axios from "axios";
import "./matchMap.css";

/*
Props:
  origin: { lat: number, lon: number }   // request location
  matches: [ { donor_id, name, blood_group, lat, lon, distance_m (optional) , ... } ]
  authToken (optional): string  // if you prefer passing token via prop; otherwise code reads localStorage.access_token
*/

const userIcon = new L.Icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// animated donor icon (HTMLDivIcon)
function createAnimatedIcon() {
  const html = `<div class="pulse-marker"><div class="pulse-core"></div></div>`;
  return L.divIcon({
    html,
    className: "animated-marker-icon",
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

export default function MatchMap({ origin, matches = [], authToken = null }) {
  const [routeGeom, setRouteGeom] = useState(null);
  const [routeInfo, setRouteInfo] = useState(null);
  const [loadingRouteFor, setLoadingRouteFor] = useState(null);
  const [mapObj, setMapObj] = useState(null);

  // compute center fallback
  const donorsWithCoords = matches.filter((m) => m.lat != null && m.lon != null);
  const center = useMemo(() => {
    if (origin?.lat && origin?.lon) return [Number(origin.lat), Number(origin.lon)];
    if (donorsWithCoords.length) return [Number(donorsWithCoords[0].lat), Number(donorsWithCoords[0].lon)];
    return [12.9716, 77.5946]; // fallback
  }, [origin, donorsWithCoords]);

  // format duration helper
  const formatDuration = (s) => {
    if (s == null) return "N/A";
    const mins = Math.round(s / 60);
    if (mins < 60) return `${mins} min`;
    const h = Math.floor(mins / 60);
    const rem = mins % 60;
    return `${h} h ${rem} min`;
  };

  // fetch route from backend API
  const fetchRoute = useCallback(async (donor) => {
    if (!origin || !origin.lat || !origin.lon || !donor) {
      console.warn("Missing origin or donor coordinates");
      return;
    }

    setLoadingRouteFor(donor.donor_id || donor.id || donor.name);
    setRouteGeom(null);
    setRouteInfo(null);

    try {
      const payload = {
        origin: { lat: Number(origin.lat), lon: Number(origin.lon) },
        destination: { lat: Number(donor.lat), lon: Number(donor.lon) }
      };

      const token = authToken || (typeof window !== "undefined" && localStorage.getItem("access_token"));
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      console.log("[MatchMap] requesting route", payload);
      const res = await axios.post("/api/route", payload, { headers, timeout: 20000 });
      console.log("[MatchMap] route response", res.data);

      let geom = res.data.geometry || [];
      // Defensive: if first coordinate looks like lon (abs > 90), swap a->b
      if (geom.length > 0 && Math.abs(geom[0][0]) > 90) {
        geom = geom.map(([a, b]) => [b, a]);
        console.log("[MatchMap] converted geometry from [lon,lat] to [lat,lon]");
      }

      // ensure numeric arrays
      geom = geom.map(pt => [Number(pt[0]), Number(pt[1])]);

      setRouteGeom(geom);
      setRouteInfo({ distance_m: res.data.distance_m, duration_s: res.data.duration_s });

      // auto-fit map bounds
      if (geom && geom.length > 0 && mapObj) {
        try {
          const bounds = L.latLngBounds(geom);
          mapObj.fitBounds(bounds, { padding: [60, 60] });
        } catch (e) {
          console.warn("fitBounds error", e);
        }
      }
    } catch (err) {
      console.error("[MatchMap] fetchRoute error:", err.response ? err.response.data : err.message);
      setRouteGeom(null);
      setRouteInfo(null);
    } finally {
      setLoadingRouteFor(null);
    }
  }, [origin, mapObj, authToken]);

  // clear route if origin changes
  useEffect(() => {
    setRouteGeom(null);
    setRouteInfo(null);
  }, [origin]);

  return (
    <div className="map-wrapper">
      <h3>📍 Map view</h3>
      <p className="map-subtitle">Blue = your request. Red pulsing = donors. Click a donor, then "Show route".</p>

      <MapContainer
        center={center}
        zoom={12}
        scrollWheelZoom={true}
        className="match-map"
        whenCreated={setMapObj}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* user origin */}
        {origin?.lat && origin?.lon && (
          <>
            <Marker position={[Number(origin.lat), Number(origin.lon)]} icon={userIcon}>
              <Popup><strong>Your request location</strong></Popup>
            </Marker>
            <Circle
              center={[Number(origin.lat), Number(origin.lon)]}
              radius={3000}
              pathOptions={{ color: "#2563eb", fillOpacity: 0.05 }}
            />
          </>
        )}

        {/* donor markers */}
        {donorsWithCoords.map((d) => {
          const key = d.donor_id || d.id || `${d.name}-${d.lat}-${d.lon}`;
          const icon = createAnimatedIcon();
          return (
            <Marker key={key} position={[Number(d.lat), Number(d.lon)]} icon={icon}>
              <Popup>
                <div style={{ minWidth: 180 }}>
                  <strong>{d.name}</strong>
                  <div>Blood: {d.blood_group || "N/A"}</div>
                  <div>Distance: {d.distance_m != null ? (d.distance_m/1000).toFixed(1) + " km" : "N/A"}</div>
                  {routeInfo && !loadingRouteFor && (
                    <div style={{ marginTop: 6, fontWeight: 700 }}>
                      Route: {formatDuration(routeInfo.duration_s)} • {routeInfo.distance_m ? (routeInfo.distance_m/1000).toFixed(1) + " km" : ""}
                    </div>
                  )}
                  <div style={{ marginTop: 8 }}>
                    <button
                      className="btn small"
                      onClick={() => fetchRoute(d)}
                      disabled={loadingRouteFor === (d.donor_id || d.id || d.name)}
                    >
                      {loadingRouteFor === (d.donor_id || d.id || d.name) ? "Loading..." : "Show route"}
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* route polyline */}
        {routeGeom && routeGeom.length > 0 && (
          <Polyline positions={routeGeom} pathOptions={{ color: "#2563eb", weight: 5, opacity: 0.9 }} />
        )}
      </MapContainer>

      {/* route info panel */}
      {routeInfo && (
        <div style={{ marginTop: 12, textAlign: "left" }} className="route-info">
          <strong>Route info:</strong>{" "}
          {routeInfo.distance_m ? `${(routeInfo.distance_m/1000).toFixed(1)} km` : "N/A"} • {formatDuration(routeInfo.duration_s)}
          <button style={{ marginLeft: 12 }} className="btn small" onClick={() => {
            setRouteGeom(null);
            setRouteInfo(null);
          }}>Clear route</button>
        </div>
      )}
    </div>
  );
}
