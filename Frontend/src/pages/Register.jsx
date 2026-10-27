import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ROLES = [
  { value: "citizen", label: "Citizen — file & track complaints" },
  { value: "official", label: "Government official — manage complaints" },
  { value: "provider", label: "Service provider — plumber, electrician, etc." },
  { value: "farmer", label: "Farmer — buy from local shops" },
  { value: "shop_owner", label: "Shop owner — sell to farmers" },
  { value: "asha_worker", label: "ASHA worker — manage patients & health records" },
];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    password: "",
    role: "citizen",
    village: "",
    official_code: "",
    asha_id: "",
    asha_code: "",
  });
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
      await register(form);
      navigate("/login", { state: { justRegistered: true } });
    } catch (err) {
      setError(err.message || "Could not create account");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-hero contour-bg">
        <div>
          <div className="eyebrow">Gram Setu</div>
          <h1>One account, every village service.</h1>
          <p>
            Your role decides what you can do — citizens file complaints, providers get found by
            neighbours, shop owners reach farmers directly.
          </p>
        </div>
        <div className="modules">
          <span className="module">01 · Community</span>
          <span className="module">02 · Local services</span>
          <span className="module">03 · Agriculture</span>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-card">
          <span className="brand">Gram Setu</span>
          <h2>Create your account</h2>
          <p className="sub">Takes less than a minute.</p>

          {error && <div className="error-banner">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="full_name">Full name</label>
              <input
                id="full_name"
                required
                value={form.full_name}
                onChange={(e) => update("full_name", e.target.value)}
                placeholder="Shravan Patil"
              />
            </div>
            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                required
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                placeholder="you@example.com"
              />
            </div>
            <div className="field">
              <label htmlFor="phone">Phone</label>
              <input
                id="phone"
                required
                value={form.phone}
                onChange={(e) => update("phone", e.target.value)}
                placeholder="9876543210"
              />
            </div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                required
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                placeholder="Choose a password"
              />
            </div>
            <div className="field">
              <label htmlFor="role">I am a...</label>
              <select id="role" value={form.role} onChange={(e) => update("role", e.target.value)}>
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            {form.role === "citizen" && (
              <div className="field">
                <label htmlFor="village">Village</label>
                <input
                  id="village"
                  value={form.village}
                  onChange={(e) => update("village", e.target.value)}
                  placeholder="e.g. Masalikatti"
                />
                <p className="hint">
                  This is used to route your complaints to the right village record.
                </p>
              </div>
            )}

            {form.role === "official" && (
              <div className="field">
                <label htmlFor="official_code">Officer code</label>
                <input
                  id="official_code"
                  required
                  value={form.official_code}
                  onChange={(e) => update("official_code", e.target.value)}
                  placeholder="Provided by the Gram Panchayat"
                />
                <p className="hint">
                  Official accounts are limited to one authorized Gram Panchayat officer — you
                  need the code they were given to register this way.
                </p>
              </div>
            )}

            {form.role === "asha_worker" && (
              <>
                <div className="field">
                  <label htmlFor="asha_id">Government ASHA Worker ID</label>
                  <input
                    id="asha_id"
                    required
                    value={form.asha_id}
                    onChange={(e) => update("asha_id", e.target.value)}
                    placeholder="e.g. ASHA-KA-8204"
                  />
                  <p className="hint">
                    Official NHM / State registration ID provided upon enrollment.
                  </p>
                </div>
                <div className="field">
                  <label htmlFor="asha_code">PHC Authorization Passcode</label>
                  <input
                    id="asha_code"
                    required
                    type="password"
                    value={form.asha_code}
                    onChange={(e) => update("asha_code", e.target.value)}
                    placeholder="Provided by Primary Health Centre"
                  />
                  <p className="hint">
                    Mandatory verification code issued by your PHC to verify healthcare personnel.
                  </p>
                </div>
              </>
            )}

            <button className="btn btn-primary" type="submit" disabled={busy}>
              {busy ? "Creating account..." : "Create account"}
            </button>
          </form>

          <div className="auth-switch">
            Already have an account? <Link to="/login">Log in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
