import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";

export default function PatientList() {
  const [patients, setPatients] = useState(null);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.listPatients().then(setPatients).catch((err) => setError(err.message));
  }, []);

  const visible = patients?.filter((p) =>
    (p.full_name || p.name || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Healthcare · AppAyu</div>
        <h1>My patients</h1>
        <p>Every patient you've registered — open one to log a visit or a screening.</p>
      </div>

      <div style={{ display: "flex", gap: 10, marginBottom: 20, maxWidth: 420 }}>
        <input placeholder="Search by name" value={search} onChange={(e) => setSearch(e.target.value)} />
        <Link to="/healthcare/patients/new" className="btn btn-gold">
          + New patient
        </Link>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!patients && !error && <p className="loading-text">Loading...</p>}

      {patients && patients.length === 0 && (
        <div className="empty-state">
          <h3>No patients yet</h3>
          <p>Register your first patient to start keeping their records.</p>
        </div>
      )}

      {visible?.map((p) => (
        <Link to={`/healthcare/patients/${p.id}`} key={p.id} style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card">
            <div className="card-title-row">
              <h3>{p.full_name || p.name}</h3>
              {p.age != null && <span className="card-meta">{p.age} yrs</span>}
            </div>
            <p className="card-meta">
              {p.gender && <span style={{ textTransform: "capitalize" }}>{p.gender}</span>}
              {p.village && ` · 🏘️ ${p.village}`}
              {p.phone && ` · 📞 ${p.phone}`}
            </p>
          </div>
        </Link>
      ))}
    </div>
  );
}
