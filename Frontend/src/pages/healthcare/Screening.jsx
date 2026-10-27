import React, { useState } from "react";

const URGENCY_STYLES = {
  routine:  { bg: "#f0f9f0", border: "#3f8f3f", color: "#2f722f", icon: "✅" },
  low:      { bg: "#fffbeb", border: "#d97706", color: "#92400e", icon: "⚠️" },
  moderate: { bg: "#fff7ed", border: "#ea580c", color: "#9a3412", icon: "🔶" },
  high:     { bg: "#fef2f2", border: "#dc2626", color: "#991b1b", icon: "🔴" },
  critical: { bg: "#fef2f2", border: "#7f1d1d", color: "#7f1d1d", icon: "🚨" },
};

const GRADE_COLORS = {
  0: "#3f8f3f", 1: "#ca8a04", 2: "#ea580c", 3: "#dc2626", 4: "#7f1d1d",
};

function UrgencyBanner({ result }) {
  const style = URGENCY_STYLES[result.urgency_level] || URGENCY_STYLES.moderate;
  return (
    <div style={{ background: style.bg, border: `2px solid ${style.border}`, borderRadius: "var(--radius)", padding: "14px 18px", marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
        <span style={{ fontSize: 20 }}>{style.icon}</span>
        <strong style={{ color: style.color, fontSize: 16 }}>{result.urgency_label}</strong>
      </div>
      <p style={{ margin: 0, color: style.color, fontSize: 14 }}>{result.action}</p>
    </div>
  );
}

function EyeResult({ result }) {
  return (
    <div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 20, flexWrap: "wrap" }}>
          <div style={{ width: 80, height: 80, borderRadius: "50%", background: GRADE_COLORS[result.grade], display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <span style={{ color: "#fff", fontSize: 28, fontWeight: 700, lineHeight: 1 }}>{result.grade}</span>
            <span style={{ color: "rgba(255,255,255,0.8)", fontSize: 10 }}>/ 4</span>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--ink)", marginBottom: 4 }}>{result.grade_name}</div>
            <div style={{ fontSize: 14, color: "var(--ink-soft)", marginBottom: 8 }}>{result.grade_description}</div>
            <div style={{ fontSize: 13, color: "var(--ink-soft)" }}>Model confidence: <strong>{result.confidence_percent}</strong></div>
          </div>
        </div>
      </div>
      <UrgencyBanner result={result} />
    </div>
  );
}

function SkinResult({ result }) {
  return (
    <div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 6 }}>{result.condition_display}</div>
        <div style={{ fontSize: 14, color: "var(--ink-soft)", marginBottom: 10 }}>{result.condition_description}</div>
        <div style={{ fontSize: 13, color: "var(--ink-soft)", marginBottom: 12 }}>
          Model confidence: <strong>{result.confidence_percent}</strong>
        </div>
        {result.top3_predictions && result.top3_predictions.length > 0 && (
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: "var(--ink-soft)", marginBottom: 8 }}>TOP 3 PREDICTIONS</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {result.top3_predictions.map((p, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 12, color: "var(--ink-soft)", width: 160, flexShrink: 0 }}>{p.display}</span>
                  <div style={{ flex: 1, height: 8, borderRadius: 4, background: "var(--line)", overflow: "hidden" }}>
                    <div style={{ width: `${p.probability}%`, height: "100%", background: i === 0 ? "var(--green)" : "var(--gold)", borderRadius: 4 }} />
                  </div>
                  <span style={{ fontSize: 12, minWidth: 40, textAlign: "right" }}>{p.probability}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      <UrgencyBanner result={result} />
    </div>
  );
}

export default function Screening({ patientId, patientName, onScreeningDone }) {
  const [screeningType, setScreeningType] = useState("eye");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  function handleTypeChange(type) {
    setScreeningType(type);
    setFile(null);
    setPreview(null);
    setResult(null);
    setError("");
  }

  function handleFileChange(e) {
    const selected = e.target.files[0];
    if (!selected) return;
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult(null);
    setError("");
  }

  async function handleSubmit() {
    if (!file) {
      setError("Please select an image first.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("photo", file);
      const token = localStorage.getItem("token");
      const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(
        `${apiUrl}/healthcare/patients/${patientId}/screening?screening_type=${screeningType}`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData }
      );
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Screening failed");
      }
      const data = await response.json();
      setResult(data);
      if (onScreeningDone) onScreeningDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const isEye = screeningType === "eye";

  return (
    <div style={{ maxWidth: 700, margin: "0 auto" }}>

      {/* Upload Section */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ margin: "0 0 4px" }}>AI Screening</h3>
        {patientName && (
          <p style={{ margin: "0 0 16px", color: "var(--ink-soft)", fontSize: 14 }}>
            Patient: <strong>{patientName}</strong>
          </p>
        )}

        {/* Screening type toggle */}
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {[
            { value: "eye", label: "👁️ Eye (Diabetic Retinopathy)" },
            { value: "skin", label: "🩺 Skin Condition" },
          ].map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleTypeChange(opt.value)}
              style={{
                flex: 1, padding: "10px 12px", borderRadius: "var(--radius)",
                border: screeningType === opt.value ? "2px solid var(--green)" : "2px solid var(--line)",
                background: screeningType === opt.value ? "#f0f9f0" : "var(--surface)",
                color: screeningType === opt.value ? "var(--green)" : "var(--ink)",
                fontWeight: screeningType === opt.value ? 700 : 400,
                cursor: "pointer", fontSize: 13,
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Image upload */}
        <div
          style={{ border: "2px dashed var(--line)", borderRadius: "var(--radius)", padding: 24, textAlign: "center", background: "var(--bg)", marginBottom: 16, cursor: "pointer" }}
          onClick={() => document.getElementById("screening-upload").click()}
        >
          {preview ? (
            <img src={preview} alt="preview" style={{ maxHeight: 220, maxWidth: "100%", borderRadius: 8, objectFit: "contain" }} />
          ) : (
            <>
              <div style={{ fontSize: 40, marginBottom: 8 }}>{isEye ? "👁️" : "🩺"}</div>
              <p style={{ margin: 0, color: "var(--ink-soft)" }}>
                {isEye ? "Click to upload a retinal fundus image" : "Click to upload a skin photo"}
              </p>
              <p style={{ margin: "4px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>JPG or PNG</p>
            </>
          )}
          <input id="screening-upload" type="file" accept="image/*" onChange={handleFileChange} style={{ display: "none" }} />
        </div>

        {error && <div className="error-banner" style={{ marginBottom: 12 }}>{error}</div>}

        <button className="btn btn-primary" onClick={handleSubmit} disabled={!file || loading} style={{ width: "100%" }}>
          {loading ? "Analyzing image... (this may take 10-30 seconds)" : "Run AI Screening"}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div>
          {isEye || result.grade !== undefined
            ? <EyeResult result={result} />
            : <SkinResult result={result} />
          }

          {/* Advice */}
          <div className="card" style={{ marginBottom: 16 }}>
            <h4 style={{ margin: "0 0 12px", color: "var(--ink)" }}>💊 Advice &amp; Recommendations</h4>
            <div style={{ fontSize: 14, color: "var(--ink)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
              {result.advice}
            </div>
          </div>

          {/* Disclaimer */}
          <div style={{ background: "#f8f8f8", border: "1px solid var(--line)", borderRadius: "var(--radius)", padding: "12px 16px", fontSize: 12, color: "var(--ink-soft)", marginBottom: 20 }}>
            ⚠️ {result.disclaimer}
          </div>

          <button className="btn btn-ghost" onClick={() => { setFile(null); setPreview(null); setResult(null); setError(""); }}>
            ← Screen another image
          </button>
        </div>
      )}
    </div>
  );
}
