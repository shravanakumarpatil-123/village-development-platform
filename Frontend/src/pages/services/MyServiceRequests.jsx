import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";

export default function MyServiceRequests() {
  const [requests, setRequests] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.myServiceRequests().then(setRequests).catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Local services · Module 2</div>
        <h1>My service requests</h1>
        <p>Every request you've sent to a provider, and its status.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!requests && !error && <p className="loading-text">Loading...</p>}

      {requests && requests.length === 0 && (
        <div className="empty-state">
          <h3>No requests yet</h3>
          <p>Find a provider in the directory and send a request — it'll show up here.</p>
        </div>
      )}

      {requests?.map((r) => (
        <div className="card" key={r.id}>
          <div className="card-title-row">
            <h3>Request #{r.id}</h3>
            <StatusBadge status={r.status} />
          </div>
          <p className="card-meta">Sent {new Date(r.created_at).toLocaleDateString()}</p>
          {r.description && <p className="card-desc">{r.description}</p>}
        </div>
      ))}
    </div>
  );
}
