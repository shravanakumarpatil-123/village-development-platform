import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";

const CERT_TYPES = ["Income", "Caste", "Residence", "Birth", "Other"];

export default function Certificates() {
  const [requests, setRequests] = useState(null);
  const [form, setForm] = useState({ certificate_type: "Income", purpose: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    api.myCertificateRequests().then(setRequests).catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.requestCertificate(form);
      setForm({ certificate_type: "Income", purpose: "" });
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Government · Certificates</div>
        <h1>Certificate requests</h1>
        <p>Request an official certificate — the Gram Panchayat will review and issue it.</p>
      </div>

      <div className="card form-card">
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="certificate_type">Certificate type</label>
            <select
              id="certificate_type"
              value={form.certificate_type}
              onChange={(e) => setForm((f) => ({ ...f, certificate_type: e.target.value }))}
            >
              {CERT_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="purpose">Purpose (optional)</label>
            <input
              id="purpose"
              value={form.purpose}
              onChange={(e) => setForm((f) => ({ ...f, purpose: e.target.value }))}
              placeholder="e.g. For a bank loan application"
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "Submitting..." : "Request certificate"}
          </button>
        </form>
      </div>

      <h3 style={{ marginTop: 26, marginBottom: 12 }}>Your requests</h3>
      {!requests && !error && <p className="loading-text">Loading...</p>}
      {requests && requests.length === 0 && (
        <div className="empty-state">
          <h3>No requests yet</h3>
          <p>Submit a request above to get started.</p>
        </div>
      )}
      {requests?.map((r) => (
        <div className="card" key={r.id}>
          <div className="card-title-row">
            <h3>{r.certificate_type} certificate</h3>
            <StatusBadge status={r.status} />
          </div>
          <p className="card-meta">Requested {new Date(r.created_at).toLocaleDateString()}</p>
          {r.purpose && <p className="card-desc">{r.purpose}</p>}
        </div>
      ))}
    </div>
  );
}
