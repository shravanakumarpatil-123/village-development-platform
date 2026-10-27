import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";

const STATUSES = ["pending", "approved", "rejected", "issued"];

export default function CertificateManager() {
  const [requests, setRequests] = useState(null);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState(null);

  function load() {
    api.allCertificateRequests().then(setRequests).catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function handleStatusChange(id, status) {
    setSavingId(id);
    try {
      await api.updateCertificateStatus(id, status);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Government · Certificates</div>
        <h1>Certificate requests</h1>
        <p>Review and issue certificates requested by citizens.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!requests && !error && <p className="loading-text">Loading...</p>}

      {requests && requests.length === 0 && (
        <div className="empty-state">
          <h3>No requests yet</h3>
          <p>Citizen certificate requests will appear here.</p>
        </div>
      )}

      {requests?.map((r) => (
        <div className="card" key={r.id}>
          <div className="card-title-row">
            <h3>{r.certificate_type} certificate</h3>
            <StatusBadge status={r.status} />
          </div>
          <div className="card-meta">
            {r.village && <span className="dept-tag">🏘️ {r.village}</span>}{" "}
            · Citizen #{r.citizen_id} · Requested {new Date(r.created_at).toLocaleDateString()}
          </div>
          {r.purpose && <p className="card-desc">{r.purpose}</p>}

          <div className="field" style={{ maxWidth: 220, marginTop: 14, marginBottom: 0 }}>
            <label>Update status</label>
            <select
              value={r.status}
              disabled={savingId === r.id}
              onChange={(e) => handleStatusChange(r.id, e.target.value)}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>
      ))}
    </div>
  );
}
