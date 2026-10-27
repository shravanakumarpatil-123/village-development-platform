import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";

export default function SchemeManager() {
  const [schemes, setSchemes] = useState(null);
  const [applications, setApplications] = useState(null);
  const [form, setForm] = useState({ title: "", description: "", eligibility: "", department: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [expandedSchemeId, setExpandedSchemeId] = useState(null);

  function load() {
    Promise.all([api.listSchemes(true), api.allSchemeApplications()])
      .then(([s, a]) => {
        setSchemes(s);
        setApplications(a);
      })
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.createScheme(form);
      setForm({ title: "", description: "", eligibility: "", department: "" });
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleToggleActive(scheme) {
    try {
      await api.updateScheme(scheme.id, { is_active: !scheme.is_active });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleAppStatus(id, status) {
    setSavingId(id);
    try {
      await api.updateSchemeApplicationStatus(id, status);
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
        <div className="eyebrow">Government · Schemes</div>
        <h1>Manage schemes</h1>
        <p>Create schemes for citizens to apply to, and review incoming applications.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="card form-card">
        <h3 style={{ marginBottom: 14 }}>Create a scheme</h3>
        <form onSubmit={handleCreate}>
          <div className="field">
            <label>Title</label>
            <input required value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} placeholder="Farmer Subsidy Scheme" />
          </div>
          <div className="field">
            <label>Description</label>
            <textarea required value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="What this scheme offers" />
          </div>
          <div className="field">
            <label>Eligibility (optional)</label>
            <input value={form.eligibility} onChange={(e) => setForm((f) => ({ ...f, eligibility: e.target.value }))} placeholder="Who can apply" />
          </div>
          <div className="field">
            <label>Department (optional)</label>
            <input value={form.department} onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))} placeholder="Agriculture" />
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "Creating..." : "Create scheme"}
          </button>
        </form>
      </div>

      <h3 style={{ marginTop: 26, marginBottom: 12 }}>All schemes</h3>
      {!schemes && <p className="loading-text">Loading...</p>}
      {schemes?.map((s) => {
        const schemeApps = applications?.filter((a) => a.scheme_id === s.id) || [];
        return (
          <div className="card" key={s.id}>
            <div className="card-title-row">
              <h3>{s.title}</h3>
              <span className={`badge ${s.is_active ? "badge-approved" : "badge-rejected"}`}>
                {s.is_active ? "active" : "inactive"}
              </span>
            </div>
            <p className="card-desc">{s.description}</p>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="btn btn-ghost btn-sm" onClick={() => handleToggleActive(s)}>
                {s.is_active ? "Deactivate" : "Reactivate"}
              </button>
              <button className="btn btn-ghost btn-sm" onClick={() => setExpandedSchemeId(expandedSchemeId === s.id ? null : s.id)}>
                {expandedSchemeId === s.id ? "Hide" : "View"} applications ({schemeApps.length})
              </button>
            </div>

            {expandedSchemeId === s.id && (
              <div style={{ marginTop: 16, borderTop: "1px solid var(--line)", paddingTop: 14 }}>
                {schemeApps.length === 0 && <p className="card-meta">No applications yet.</p>}
                {schemeApps.map((a) => (
                  <div className="list-row" key={a.id} style={{ alignItems: "flex-start" }}>
                    <div>
                      <span className="card-meta">
                        Citizen #{a.citizen_id} {a.village && `· ${a.village}`}
                      </span>
                      {a.note && <p className="card-desc" style={{ margin: "4px 0 0" }}>{a.note}</p>}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <StatusBadge status={a.status} />
                      {a.status === "pending" && (
                        <>
                          <button className="btn btn-gold btn-sm" disabled={savingId === a.id} onClick={() => handleAppStatus(a.id, "approved")}>
                            Approve
                          </button>
                          <button className="btn btn-ghost btn-sm" disabled={savingId === a.id} onClick={() => handleAppStatus(a.id, "rejected")}>
                            Reject
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
