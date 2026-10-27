import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../../api/client";
import Screening from "./Screening";

export default function PatientDetail() {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [history, setHistory] = useState([]);
  const [screenings, setScreenings] = useState([]);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("history");

  const [historyForm, setHistoryForm] = useState({ condition: "", notes: "" });
  const [historyBusy, setHistoryBusy] = useState(false);
  const [historyError, setHistoryError] = useState("");

  function load() {
    api.getPatient(patientId)
      .then(setPatient)
      .catch((err) => setError(err.message));

    api.listMedicalHistory(patientId)
      .then(setHistory)
      .catch(() => setHistory([]));

    api.listPatientScreenings(patientId)
      .then((data) => {
        if (Array.isArray(data)) setScreenings(data);
        else if (data && Array.isArray(data.screenings)) setScreenings(data.screenings);
        else setScreenings([]);
      })
      .catch(() => setScreenings([]));
  }

  useEffect(load, [patientId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleAddHistory(e) {
    e.preventDefault();
    setHistoryError("");
    setHistoryBusy(true);
    try {
      await api.addMedicalHistory(patientId, historyForm);
      setHistoryForm({ condition: "", notes: "" });
      load();
    } catch (err) {
      setHistoryError(err.message);
    } finally {
      setHistoryBusy(false);
    }
  }

  if (!patient && !error) return <p className="loading-text">Loading...</p>;
  if (error && !patient) return <div className="error-banner">{error}</div>;

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Healthcare · AppAyu</div>
        <Link to="/healthcare/patients" style={{ fontSize: 13 }}>← Back to patients</Link>
        <h1 style={{ marginTop: 8 }}>{patient?.full_name || patient?.name}</h1>
        <p>
          {patient?.age != null && `${patient.age} yrs`}
          {patient?.gender && ` · ${patient.gender}`}
          {patient?.village && ` · 🏘️ ${patient.village}`}
          {patient?.phone && ` · 📞 ${patient.phone}`}
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24, borderBottom: "1px solid var(--line)", paddingBottom: 0 }}>
        {[
          { key: "history", label: "📋 Medical History" },
          { key: "screening", label: "🔬 AI Screening" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              background: "none", border: "none",
              borderBottom: activeTab === tab.key ? "3px solid var(--green)" : "3px solid transparent",
              padding: "10px 16px", cursor: "pointer",
              fontWeight: activeTab === tab.key ? 700 : 400,
              color: activeTab === tab.key ? "var(--green)" : "var(--ink-soft)",
              fontSize: 14, marginBottom: -1,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Medical History Tab */}
      {activeTab === "history" && (
        <div>
          <div className="card form-card" style={{ marginBottom: 20 }}>
            <h3 style={{ margin: "0 0 16px" }}>Add visit record</h3>
            {historyError && <div className="error-banner">{historyError}</div>}
            <form onSubmit={handleAddHistory}>
              <div className="field">
                <label>Condition / diagnosis</label>
                <input
                  required
                  value={historyForm.condition}
                  onChange={(e) => setHistoryForm((f) => ({ ...f, condition: e.target.value }))}
                  placeholder="e.g. Type 2 Diabetes, Viral fever"
                />
              </div>
              <div className="field">
                <label>Notes (optional)</label>
                <textarea
                  value={historyForm.notes}
                  onChange={(e) => setHistoryForm((f) => ({ ...f, notes: e.target.value }))}
                  placeholder="Treatment given, follow-up needed, etc."
                />
              </div>
              <button className="btn btn-primary" type="submit" disabled={historyBusy}>
                {historyBusy ? "Saving..." : "Add visit record"}
              </button>
            </form>
          </div>

          {history.length === 0 ? (
            <div className="empty-state">
              <h3>No history recorded yet</h3>
              <p>Add the first visit record above.</p>
            </div>
          ) : history.map((h) => (
            <div className="card" key={h.id} style={{ marginBottom: 12 }}>
              <div className="card-title-row">
                <h3>{h.condition}</h3>
                <span className="card-meta">
                  {new Date(h.visit_date || h.created_at).toLocaleDateString("en-IN", {
                    day: "numeric", month: "short", year: "numeric"
                  })}
                </span>
              </div>
              {h.notes && <p className="card-desc" style={{ marginTop: 6 }}>{h.notes}</p>}
            </div>
          ))}
        </div>
      )}

      {/* AI Screening Tab */}
      {activeTab === "screening" && (
        <div>
          {/* Screening component — now handles both eye and skin */}
          <Screening
            patientId={patientId}
            patientName={patient?.full_name}
            onScreeningDone={load}
          />

          {/* Past screenings */}
          {screenings.length > 0 && (
            <div style={{ marginTop: 32 }}>
              <h3 style={{ marginBottom: 12 }}>Past screenings</h3>
              {screenings.map((s) => (
                <div className="card" key={s.id} style={{ marginBottom: 12 }}>
                  <div className="card-title-row">
                    <h3 style={{ textTransform: "capitalize" }}>
                      {s.screening_type || "eye"} screening
                    </h3>
                    <span className="card-meta">
                      {new Date(s.created_at).toLocaleDateString("en-IN", {
                        day: "numeric", month: "short", year: "numeric"
                      })}
                    </span>
                  </div>
                  {s.prediction ? (
                    <p className="card-desc" style={{ marginTop: 6 }}>
                      {s.prediction}
                      {s.confidence && (
                        <span style={{ color: "var(--ink-soft)", marginLeft: 8 }}>
                          ({Math.round(s.confidence * 100)}% confidence)
                        </span>
                      )}
                    </p>
                  ) : (
                    <p className="card-meta" style={{ marginTop: 6 }}>Awaiting model integration</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
