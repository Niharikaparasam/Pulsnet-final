// src/components/MatchesTable.jsx
import React from "react";

const MatchesTable = ({ matches }) => {
  if (!matches || matches.length === 0) {
    return <p className="muted">No matches yet.</p>;
  }

  return (
    <div className="table-wrapper">
      <table className="matches-table">
        <thead>
          <tr>
            <th>Donor ID</th>
            <th>Name</th>
            <th>Blood</th>
            <th>Phone</th>
            <th>Distance (km)</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((d) => (
            <tr key={d.donor_id}>
              <td>{d.donor_id}</td>
              <td>{d.name}</td>
              <td>{d.blood_group}</td>
              <td>{d.phone}</td>
              <td>
                {d.distance_m != null
                  ? (d.distance_m / 1000).toFixed(1)
                  : "N/A"}
              </td>
              
              <td>{d.score?.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default MatchesTable;
