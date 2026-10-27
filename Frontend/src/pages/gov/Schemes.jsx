import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";

export default function Schemes() {
  const [schemes, setSchemes] = useState(null);
  const [myApplications, setMyApplications] = useState([]);
  const [error, setError] = useState("");
  const [notes, setNotes] = useState({});
  const [appliedIds, setAppliedIds] = useState(new Set());

  function load() {
    Promise.all([api.listSchemes(), api.mySchemeApplications()])
      .then(([schemesData, apps]) => {
        setSchemes(schemesData);
        setMyApplications(apps);
        setAppliedIds(new Set(apps.map((a) => a.scheme_id)));
      })
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function handleApply(schemeId) {
    setError("");
    try {
      await api.applyToScheme(schemeId, notes[schemeId] || "");
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  function applicationFor(schemeId) {
    return myApplications.find((a) => a.scheme_id === schemeId);
  }

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Government · Schemes</div>
        <h1>Government schemes</h1>
        <p>Browse active schemes and apply directly — your application goes straight to the Gram Panchayat.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!schemes && !error && <p className="loading-text">Loading...</p>}

      {schemes && schemes.length === 0 && (
        <div className="empty-state">
          <h3>No schemes available right now</h3>
          <p>Check back later — officials add new schemes here as they become available.</p>
        </div>
      )}

      {schemes?.map((s) => {
        const myApp = applicationFor(s.id);
        return (
          <div className="card" key={s.id}>
            <div className="card-title-row">
              <h3>{s.title}</h3>
              {s.department && <span className="dept-tag">{s.department}</span>}
            </div>
            <p className="card-desc">{s.description}</p>
            {s.eligibility && (
              <p className="card-meta" style={{ marginTop: 8 }}>
                <strong>Eligibility:</strong> {s.eligibility}
              </p>
            )}

            <div style={{ marginTop: 14 }}>
              {myApp ? (
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className="card-meta">You applied on {new Date(myApp.created_at).toLocaleDateString()}</span>
                  <StatusBadge status={myApp.status} />
                </div>
              ) : (
                <div style={{ display: "flex", gap: 8, maxWidth: 460, flexWrap: "wrap" }}>
                  <input
                    placeholder="Optional note (why you're applying)"
                    onChange={(e) => setNotes((n) => ({ ...n, [s.id]: e.target.value }))}
                  />
                  <button className="btn btn-gold btn-sm" onClick={() => handleApply(s.id)}>
                    Apply
                  </button>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
