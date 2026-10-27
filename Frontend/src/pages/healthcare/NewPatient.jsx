import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";

export default function NewPatient() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", age: "", gender: "", phone: "", village: "", address: "" });
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
      const patient = await api.registerPatient({
        full_name: form.full_name,
        age: form.age ? parseInt(form.age, 10) : null,
        gender: form.gender || null,
        phone: form.phone || null,
        village: form.village || null,
        address: form.address || null,
      });
      navigate(`/healthcare/patients/${patient.id}`);
    } catch (err) {
      setError(err.message || "Could not register patient");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Healthcare · AppAyu</div>
        <h1>Register a patient</h1>
        <p>Basic details now — you can add medical history and screenings after.</p>
      </div>

      <div className="card form-card">
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="full_name">Full name</label>
            <input id="full_name" required value={form.full_name} onChange={(e) => update("full_name", e.target.value)} placeholder="Ramesh Kumar" />
          </div>
          <div className="two-col">
            <div className="field">
              <label htmlFor="age">Age</label>
              <input id="age" type="number" value={form.age} onChange={(e) => update("age", e.target.value)} placeholder="45" />
            </div>
            <div className="field">
              <label htmlFor="gender">Gender</label>
              <select id="gender" value={form.gender} onChange={(e) => update("gender", e.target.value)}>
                <option value="">Not specified</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div className="field">
            <label htmlFor="phone">Phone (optional)</label>
            <input id="phone" value={form.phone} onChange={(e) => update("phone", e.target.value)} placeholder="9876543210" />
          </div>
          <div className="field">
            <label htmlFor="village">Village</label>
            <input id="village" value={form.village} onChange={(e) => update("village", e.target.value)} placeholder="Sangameshwar" />
          </div>
          <div className="field">
            <label htmlFor="address">Address (optional)</label>
            <input id="address" value={form.address} onChange={(e) => update("address", e.target.value)} placeholder="House number, street" />
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "Registering..." : "Register patient"}
          </button>
        </form>
      </div>
    </div>
  );
}
