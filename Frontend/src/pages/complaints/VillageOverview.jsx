import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";

export default function VillageOverview() {
  const [villages, setVillages] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.villageSummary().then(setVillages).catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Community · Government dashboard</div>
        <h1>Villages</h1>
        <p>Every village under your Gram Panchayat that has filed complaints. Pick one to review.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!villages && !error && <p className="loading-text">Loading...</p>}

      {villages && villages.length === 0 && (
        <div className="empty-state">
          <h3>No complaints yet</h3>
          <p>Once citizens start filing complaints with a village set, they'll appear here.</p>
        </div>
      )}

      {villages?.map((v) => (
        <div className="card" key={v.village}>
          <div className="card-title-row">
            <h3>{v.village}</h3>
            <span className="dept-tag">
              {v.complaint_count} complaint{v.complaint_count !== 1 ? "s" : ""}
            </span>
          </div>
          <div style={{ marginTop: 14 }}>
            <Link
              to={`/complaints/dashboard?village=${encodeURIComponent(v.village)}`}
              className="btn btn-gold btn-sm"
            >
              View complaints
            </Link>
          </div>
        </div>
      ))}

      {villages && villages.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <Link to="/complaints/dashboard" className="btn btn-ghost btn-sm">
            View all villages together
          </Link>
        </div>
      )}
    </div>
  );
}
