import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";

export default function Shops() {
  const [shops, setShops] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listShops().then(setShops).catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Agriculture · Module 3</div>
        <h1>Shops</h1>
        <p>Every registered shop on the platform.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!shops && !error && <p className="loading-text">Loading...</p>}

      {shops && shops.length === 0 && (
        <div className="empty-state">
          <h3>No shops yet</h3>
          <p>Shop owners can register from their dashboard.</p>
        </div>
      )}

      {shops?.map((s) => (
        <div className="card" key={s.id}>
          <div className="card-title-row">
            <h3>{s.name}</h3>
          </div>
          {s.location && <p className="card-meta">📍 {s.location}</p>}
          <div style={{ marginTop: 14 }}>
            <Link to={`/agriculture/products?shop=${s.id}`} className="btn btn-ghost btn-sm">
              View products
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}
