import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const justRegistered = location.state?.justRegistered;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.message || "Could not log in");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-hero contour-bg">
        <div>
          <div className="eyebrow">Gram Setu</div>
          <h1>The bridge between every household and the village office.</h1>
          <p>
            File complaints, find trusted local service providers, and connect farmers directly
            with shops — all from one place.
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
          <h2>Welcome back</h2>
          <p className="sub">Log in to continue.</p>

          {justRegistered && !error && (
            <div className="success-banner">Account created — log in to continue.</div>
          )}
          {error && <div className="error-banner">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="email">Email, Phone, or ASHA Worker ID</label>
              <input
                id="email"
                type="text"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com, phone, or ASHA-XXXX"
              />
            </div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {busy ? "Logging in..." : "Log in"}
            </button>
          </form>

          <div className="auth-switch">
            New here? <Link to="/register">Create an account</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
