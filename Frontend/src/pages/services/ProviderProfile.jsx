import React, { useEffect, useState } from "react";
import { api } from "../../api/client";

export default function ProviderProfile() {
  const [form, setForm] = useState({ service_type: "", description: "", latitude: "", longitude: "" });
  const [isAvailable, setIsAvailable] = useState(true);
  const [existingProfile, setExistingProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .myProviderProfile()
      .then((p) => {
        setExistingProfile(p);
        setForm({
          service_type: p.service_type || "",
          description: p.description || "",
          latitude: p.latitude ?? "",
          longitude: p.longitude ?? "",
        });
        setIsAvailable(p.is_available);
      })
      .catch(() => {
        // No profile yet — that's fine, show the create form
      })
      .finally(() => setLoading(false));
  }, []);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");
    setBusy(true);
    const payload = {
      service_type: form.service_type,
      description: form.description,
      latitude: form.latitude !== "" ? parseFloat(form.latitude) : null,
      longitude: form.longitude !== "" ? parseFloat(form.longitude) : null,
    };
    try {
      if (existingProfile) {
        const updated = await api.updateMyProviderProfile(payload);
        setExistingProfile(updated);
        setSuccess("Profile updated.");
      } else {
        const created = await api.becomeProvider(payload);
        setExistingProfile(created);
        setIsAvailable(created.is_available);
        setSuccess("Profile saved — you're now listed in the directory.");
      }
    } catch (err) {
      setError(err.message || "Could not save profile");
    } finally {
      setBusy(false);
    }
  }

  async function handleToggleAvailability() {
    setError("");
    const next = !isAvailable;
    setIsAvailable(next); // optimistic
    try {
      const updated = await api.updateMyProviderProfile({ is_available: next });
      setExistingProfile(updated);
    } catch (err) {
      setIsAvailable(!next); // revert on failure
      setError(err.message || "Could not update availability");
    }
  }

  if (loading) {
    return <p className="loading-text">Loading...</p>;
  }

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Local services · Module 2</div>
        <h1>My provider profile</h1>
        <p>Set your service type and location so nearby households can find you.</p>
      </div>

      {existingProfile && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-title-row">
            <h3>Availability</h3>
            <span className={`badge ${isAvailable ? "badge-approved" : "badge-rejected"}`}>
              {isAvailable ? "available" : "unavailable"}
            </span>
          </div>
          <p className="card-desc">
            Toggle this off temporarily if you're busy or on leave — you'll be hidden from the
            directory until you switch it back on.
          </p>
          <button className="btn btn-ghost btn-sm" style={{ marginTop: 10 }} onClick={handleToggleAvailability}>
            Mark myself {isAvailable ? "unavailable" : "available"}
          </button>
        </div>
      )}

      <div className="card form-card">
        {error && <div className="error-banner">{error}</div>}
        {success && <div className="success-banner">{success}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="service_type">Service type</label>
            <input
              id="service_type"
              required
              value={form.service_type}
              onChange={(e) => update("service_type", e.target.value)}
              placeholder="Plumber, electrician, tutor..."
            />
          </div>
          <div className="field">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              placeholder="Years of experience, specialties, availability..."
            />
          </div>
          <div className="two-col">
            <div className="field">
              <label htmlFor="latitude">Latitude (optional)</label>
              <input
                id="latitude"
                value={form.latitude}
                onChange={(e) => update("latitude", e.target.value)}
                placeholder="17.3850"
              />
            </div>
            <div className="field">
              <label htmlFor="longitude">Longitude (optional)</label>
              <input
                id="longitude"
                value={form.longitude}
                onChange={(e) => update("longitude", e.target.value)}
                placeholder="78.4867"
              />
            </div>
          </div>
          <p className="hint" style={{ marginBottom: 16 }}>
            Adding coordinates lets nearby search find you — you can leave this blank for now.
          </p>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "Saving..." : existingProfile ? "Save changes" : "Save profile"}
          </button>
        </form>
      </div>
    </div>
  );
}
