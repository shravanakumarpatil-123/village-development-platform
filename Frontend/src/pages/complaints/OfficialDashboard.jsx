import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, fileUrl } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";
import CommentsThread from "../../components/CommentsThread";

const STATUSES = ["submitted", "in_progress", "resolved", "rejected"];
const PRIORITY_COLORS = {
  low: "badge-submitted",
  medium: "badge-pending",
  high: "badge-in_progress",
  urgent: "badge-rejected",
};
const PRIORITY_ORDER = { urgent: 0, high: 1, medium: 2, low: 3 };

export default function OfficialDashboard() {
  const [searchParams] = useSearchParams();
  const initialVillage = searchParams.get("village") || "";

  const [complaints, setComplaints] = useState(null);
  const [villages, setVillages] = useState([]);
  const [villageFilter, setVillageFilter] = useState(initialVillage);
  const [sortByPriority, setSortByPriority] = useState(true);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState(null);
  const [openId, setOpenId] = useState(null);

  function load(village) {
    api
      .allComplaints(village)
      .then(setComplaints)
      .catch((err) => setError(err.message));
  }

  useEffect(() => {
    load(initialVillage || undefined);
    api.listComplaintVillages().then(setVillages).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleVillageChange(v) {
    setVillageFilter(v);
    load(v || undefined);
  }

  async function handleStatusChange(id, status) {
    setSavingId(id);
    try {
      await api.updateComplaintStatus(id, status);
      load(villageFilter || undefined);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingId(null);
    }
  }

  const sortedComplaints = complaints
    ? [...complaints].sort((a, b) =>
        sortByPriority ? PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority] : 0
      )
    : null;

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Community · Government dashboard</div>
        <h1>{villageFilter ? `Complaints — ${villageFilter}` : "All complaints"}</h1>
        <p>Review what citizens have reported, and update each one's status.</p>
        <Link to="/complaints/villages" style={{ fontSize: 13 }}>
          ← Back to villages
        </Link>
      </div>

      <div style={{ display: "flex", gap: 20, flexWrap: "wrap", marginTop: 20, marginBottom: 20 }}>
        {villages.length > 0 && (
          <div className="field" style={{ maxWidth: 260, marginBottom: 0 }}>
            <label htmlFor="village-filter">Filter by village</label>
            <select
              id="village-filter"
              value={villageFilter}
              onChange={(e) => handleVillageChange(e.target.value)}
            >
              <option value="">All villages</option>
              {villages.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>
        )}
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, marginTop: villages.length > 0 ? 24 : 0 }}>
          <input type="checkbox" checked={sortByPriority} onChange={(e) => setSortByPriority(e.target.checked)} style={{ width: "auto" }} />
          Sort by priority (urgent first)
        </label>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!complaints && !error && <p className="loading-text">Loading...</p>}

      {complaints && complaints.length === 0 && (
        <div className="empty-state">
          <h3>Nothing filed yet</h3>
          <p>New complaints from citizens will appear here.</p>
        </div>
      )}

      {sortedComplaints?.map((c) => (
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
            {c.village && <span className="dept-tag">🏘️ {c.village}</span>}{" "}
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

          <div className="field" style={{ maxWidth: 220, marginTop: 14, marginBottom: 0 }}>
            <label>Update status</label>
            <select
              value={c.status}
              disabled={savingId === c.id}
              onChange={(e) => handleStatusChange(c.id, e.target.value)}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>

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
