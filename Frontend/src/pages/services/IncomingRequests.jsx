import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";

const NEXT_STATUSES = ["pending", "accepted", "completed", "cancelled"];

export default function IncomingRequests() {
  const [requests, setRequests] = useState(null);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState(null);

  function load() {
    api
      .incomingServiceRequests()
      .then(setRequests)
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function handleStatusChange(id, status) {
    setSavingId(id);
    try {
      await api.updateServiceRequestStatus(id, status);
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
        <div className="eyebrow">Local services · Module 2</div>
        <h1>Incoming requests</h1>
        <p>Requests people have sent to you — update the status as you work through them.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!requests && !error && <p className="loading-text">Loading...</p>}

      {requests && requests.length === 0 && (
        <div className="empty-state">
          <h3>No requests yet</h3>
          <p>
            Make sure you've filled out "My provider profile" — that's what makes you visible in
            the directory so people can find and request you.
          </p>
        </div>
      )}

      {requests?.map((r) => (
        <div className="card" key={r.id}>
          <div className="card-title-row">
            <h3>Request #{r.id}</h3>
            <StatusBadge status={r.status} />
          </div>
          <p className="card-meta">Received {new Date(r.created_at).toLocaleDateString()}</p>
          {r.description && <p className="card-desc">{r.description}</p>}

          <div className="field" style={{ maxWidth: 220, marginTop: 14, marginBottom: 0 }}>
            <label>Update status</label>
            <select
              value={r.status}
              disabled={savingId === r.id}
              onChange={(e) => handleStatusChange(r.id, e.target.value)}
            >
              {NEXT_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>
      ))}
    </div>
  );
}
