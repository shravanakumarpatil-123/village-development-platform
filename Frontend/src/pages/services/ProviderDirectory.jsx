import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";

function Stars({ value }) {
  const full = Math.round(value);
  return <span className="stars">{"★".repeat(full)}{"☆".repeat(5 - full)}</span>;
}

function ReviewsPanel({ providerId }) {
  const [reviews, setReviews] = useState(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  function load() {
    api.providerReviews(providerId).then(setReviews).catch((err) => setError(err.message));
  }

  useEffect(load, [providerId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.leaveReview({ provider_id: providerId, rating: Number(rating), comment });
      setComment("");
      setSent(true);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={{ marginTop: 16, borderTop: "1px solid var(--line)", paddingTop: 14 }}>
      {error && <div className="error-banner">{error}</div>}
      {reviews === null && <p className="loading-text">Loading reviews...</p>}
      {reviews?.length === 0 && <p className="card-meta">No reviews yet — be the first.</p>}
      {reviews?.map((r) => (
        <div className="list-row" key={r.id} style={{ alignItems: "flex-start" }}>
          <div>
            <Stars value={r.rating} />
            {r.comment && <p className="card-desc" style={{ margin: "4px 0 0" }}>{r.comment}</p>}
          </div>
          <span className="card-meta">{new Date(r.created_at).toLocaleDateString()}</span>
        </div>
      ))}

      {sent ? (
        <p className="success-banner" style={{ marginTop: 12 }}>Thanks for your review.</p>
      ) : (
        <form onSubmit={handleSubmit} style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <select value={rating} onChange={(e) => setRating(e.target.value)} style={{ maxWidth: 100 }}>
            {[5, 4, 3, 2, 1].map((n) => (
              <option key={n} value={n}>{n} star{n > 1 ? "s" : ""}</option>
            ))}
          </select>
          <input
            placeholder="Leave a comment (optional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            style={{ flex: 1, minWidth: 180 }}
          />
          <button className="btn btn-ghost btn-sm" type="submit">Post review</button>
        </form>
      )}
    </div>
  );
}

export default function ProviderDirectory() {
  const { user } = useAuth();
  const [providers, setProviders] = useState(null);
  const [serviceType, setServiceType] = useState("");
  const [nearbyCoords, setNearbyCoords] = useState(null); // { latitude, longitude }
  const [radiusKm, setRadiusKm] = useState(10);
  const [locating, setLocating] = useState(false);
  const [error, setError] = useState("");
  const [requestedId, setRequestedId] = useState(null);
  const [note, setNote] = useState("");
  const [openReviewsId, setOpenReviewsId] = useState(null);

  function load(coords = nearbyCoords) {
    const params = { service_type: serviceType };
    if (coords) {
      params.latitude = coords.latitude;
      params.longitude = coords.longitude;
      params.radius_km = radiusKm;
    }
    api
      .searchProviders(params)
      .then(setProviders)
      .catch((err) => setError(err.message));
  }

  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleSearch(e) {
    e.preventDefault();
    load();
  }

  function handleUseMyLocation() {
    setError("");
    if (!navigator.geolocation) {
      setError("Your browser doesn't support location access.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
        setNearbyCoords(coords);
        setLocating(false);
        load(coords);
      },
      () => {
        setError("Couldn't get your location — check your browser's location permission.");
        setLocating(false);
      }
    );
  }

  function handleClearLocation() {
    setNearbyCoords(null);
    load(null);
  }

  async function handleRequest(providerId) {
    setError("");
    setNote("");
    try {
      await api.requestService({ provider_id: providerId, description: note });
      setRequestedId(providerId);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Local services · Module 2</div>
        <h1>Find a service provider</h1>
        <p>Search by service type, then send a request directly.</p>
      </div>

      <form onSubmit={handleSearch} style={{ display: "flex", gap: 10, marginBottom: 12, maxWidth: 420, flexWrap: "wrap" }}>
        <input
          placeholder="e.g. plumber, electrician"
          value={serviceType}
          onChange={(e) => setServiceType(e.target.value)}
        />
        <button className="btn btn-ghost" type="submit">
          Search
        </button>
      </form>

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
        {!nearbyCoords ? (
          <button className="btn btn-ghost btn-sm" onClick={handleUseMyLocation} disabled={locating}>
            {locating ? "Getting location..." : "📍 Search near me"}
          </button>
        ) : (
          <>
            <span className="dept-tag">Within {radiusKm}km of you</span>
            <select
              value={radiusKm}
              onChange={(e) => {
                const r = Number(e.target.value);
                setRadiusKm(r);
                load({ ...nearbyCoords });
              }}
              style={{ maxWidth: 120 }}
            >
              {[5, 10, 20, 50].map((r) => (
                <option key={r} value={r}>{r} km</option>
              ))}
            </select>
            <button className="btn btn-ghost btn-sm" onClick={handleClearLocation}>
              Clear
            </button>
          </>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!providers && !error && <p className="loading-text">Loading...</p>}

      {providers && providers.length === 0 && (
        <div className="empty-state">
          <h3>No providers found</h3>
          <p>Try a different search term, or check back later.</p>
        </div>
      )}

      {providers?.map((p) => (
        <div className="card" key={p.id}>
          <div className="card-title-row">
            <h3 style={{ textTransform: "capitalize" }}>{p.service_type}</h3>
            <span className={`badge ${p.is_available ? "badge-approved" : "badge-rejected"}`}>
              {p.is_available ? "available" : "unavailable"}
            </span>
          </div>
          {p.description && <p className="card-desc">{p.description}</p>}

          <div className="card-meta" style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
            {p.average_rating != null ? (
              <>
                <Stars value={p.average_rating} /> {p.average_rating} ({p.review_count})
              </>
            ) : (
              "No ratings yet"
            )}
            <button
              className="btn btn-ghost btn-sm"
              style={{ marginLeft: "auto" }}
              onClick={() => setOpenReviewsId(openReviewsId === p.id ? null : p.id)}
            >
              {openReviewsId === p.id ? "Hide reviews" : "Reviews"}
            </button>
          </div>

          {openReviewsId === p.id && <ReviewsPanel providerId={p.id} />}

          {user && user.id !== p.user_id && (
            <div style={{ marginTop: 14 }}>
              {requestedId === p.id ? (
                <span className="success-banner" style={{ display: "inline-block", margin: 0 }}>
                  Request sent
                </span>
              ) : (
                <div style={{ display: "flex", gap: 8, maxWidth: 420 }}>
                  <input
                    placeholder="What do you need help with?"
                    onChange={(e) => setNote(e.target.value)}
                  />
                  <button className="btn btn-gold btn-sm" onClick={() => handleRequest(p.id)}>
                    Request
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
