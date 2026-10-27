import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, fileUrl } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";
import CommentsThread from "../../components/CommentsThread";

const PRIORITY_COLORS = {
  low: "badge-submitted",
  medium: "badge-pending",
  high: "badge-in_progress",
  urgent: "badge-rejected",
};

export default function MyComplaints() {
  const [complaints, setComplaints] = useState(null);
  const [error, setError] = useState("");
  const [openId, setOpenId] = useState(null);

  useEffect(() => {
    api
      .myComplaints()
      .then(setComplaints)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Community · Module 1</div>
        <h1>My complaints</h1>
        <p>Every complaint you've filed, and where it stands.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {!complaints && !error && <p className="loading-text">Loading...</p>}

      {complaints && complaints.length === 0 && (
        <div className="empty-state">
          <h3>No complaints yet</h3>
          <p>When you report an issue, it'll show up here with live status updates.</p>
          <div style={{ marginTop: 14 }}>
            <Link to="/complaints/new" className="btn btn-gold btn-sm">
              File a complaint
            </Link>
          </div>
        </div>
      )}

      {complaints?.map((c) => (
        <div className="card" key={c.id}>
          <div className="card-title-row">
            <h3>{c.title}</h3>
            <StatusBadge status={c.status} />
          </div>
          <div className="card-meta">
            {c.department && <span className="dept-tag">{c.department}</span>}{" "}
            <span className={`badge ${PRIORITY_COLORS[c.priority] || "badge-submitted"}`}>
              {c.priority}
            </span>{" "}
            · Filed {new Date(c.created_at).toLocaleDateString()}
          </div>
          <p className="card-desc">{c.description}</p>
          {c.location && <p className="card-meta">📍 {c.location}</p>}
          {c.photo_url && (
            <img
              src={fileUrl(c.photo_url)}
              alt="Complaint evidence"
              style={{ maxWidth: 220, borderRadius: 8, marginTop: 10, display: "block" }}
            />
          )}

          <div style={{ marginTop: 12 }}>
            <button className="btn btn-ghost btn-sm" onClick={() => setOpenId(openId === c.id ? null : c.id)}>
              {openId === c.id ? "Hide comments" : "View / add comments"}
            </button>
          </div>

          {openId === c.id && <CommentsThread complaintId={c.id} />}
        </div>
      ))}
    </div>
  );
}
