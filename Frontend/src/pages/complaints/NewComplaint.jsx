import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";

const PRIORITIES = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
];

export default function NewComplaint() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: "", description: "", location: "", priority: "medium" });
  const [photo, setPhoto] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const complaint = await api.createComplaint(form);
      if (photo) {
        await api.uploadComplaintPhoto(complaint.id, photo);
      }
      navigate("/complaints/mine");
    } catch (err) {
      setError(err.message || "Could not submit complaint");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Community · Module 1</div>
        <h1>File a complaint</h1>
        <p>Describe the issue clearly — it's automatically routed to the right department.</p>
      </div>

      <div className="card form-card">
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="title">Title</label>
            <input
              id="title"
              required
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              placeholder="Street light not working"
            />
          </div>
          <div className="field">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              required
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              placeholder="Give as much detail as you can — this helps route it correctly."
            />
          </div>
          <div className="field">
            <label htmlFor="location">Location (optional)</label>
            <input
              id="location"
              value={form.location}
              onChange={(e) => update("location", e.target.value)}
              placeholder="Main Road, near the temple"
            />
          </div>
          <div className="field">
            <label htmlFor="priority">Priority</label>
            <select id="priority" value={form.priority} onChange={(e) => update("priority", e.target.value)}>
              {PRIORITIES.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
            <p className="hint">How urgent is this? Use "Urgent" only for safety issues.</p>
          </div>
          <div className="field">
            <label htmlFor="photo">Photo evidence (optional)</label>
            <input
              id="photo"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => setPhoto(e.target.files?.[0] || null)}
            />
            <p className="hint">JPG, PNG, or WEBP, up to 5MB.</p>
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "Submitting..." : "Submit complaint"}
          </button>
        </form>
      </div>
    </div>
  );
}
