import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";

export default function MyProductRequests() {
  const [requests, setRequests] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.myProductRequests().then(setRequests).catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Agriculture · Module 3</div>
        <h1>My product requests</h1>
        <p>Everything you've requested from local shops, and its status.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!requests && !error && <p className="loading-text">Loading...</p>}

      {requests && requests.length === 0 && (
        <div className="empty-state">
          <h3>No requests yet</h3>
          <p>Browse products and request stock — it'll show up here.</p>
        </div>
      )}

      {requests?.map((r) => (
        <div className="card" key={r.id}>
          <div className="card-title-row">
            <h3>Product #{r.product_id} · Qty {r.quantity}</h3>
            <StatusBadge status={r.status} />
          </div>
          <p className="card-meta">
            Requested {new Date(r.created_at).toLocaleDateString()}
            {r.batch_id && " · part of a multi-item order"}
          </p>
        </div>
      ))}
    </div>
  );
}
