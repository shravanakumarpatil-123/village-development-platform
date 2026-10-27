import React, { useEffect, useState } from "react";
import { api } from "../api/client";

export default function CommentsThread({ complaintId }) {
  const [comments, setComments] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    api.complaintComments(complaintId).then(setComments).catch((err) => setError(err.message));
  }

  useEffect(load, [complaintId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSubmit(e) {
    e.preventDefault();
    if (!message.trim()) return;
    setError("");
    setBusy(true);
    try {
      await api.addComplaintComment(complaintId, message.trim());
      setMessage("");
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ marginTop: 16, borderTop: "1px solid var(--line)", paddingTop: 14 }}>
      {error && <div className="error-banner">{error}</div>}
      {comments === null && <p className="loading-text">Loading comments...</p>}
      {comments?.length === 0 && <p className="card-meta">No comments yet.</p>}

      {comments?.map((c) => (
        <div className="list-row" key={c.id} style={{ alignItems: "flex-start" }}>
          <div>
            <span className="card-meta" style={{ fontWeight: 600 }}>
              {c.author_name} {c.author_role === "official" && "(Official)"}
            </span>
            <p className="card-desc" style={{ margin: "2px 0 0" }}>{c.message}</p>
          </div>
          <span className="card-meta">{new Date(c.created_at).toLocaleDateString()}</span>
        </div>
      ))}

      <form onSubmit={handleSubmit} style={{ marginTop: 14, display: "flex", gap: 8 }}>
        <input
          placeholder="Add a comment..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button className="btn btn-ghost btn-sm" type="submit" disabled={busy}>
          {busy ? "Posting..." : "Post"}
        </button>
      </form>
    </div>
  );
}
