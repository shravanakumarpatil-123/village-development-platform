import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const CARDS_BY_ROLE = {
  citizen: [
    { to: "/complaints/new", title: "File a complaint", desc: "Report an issue — it's automatically routed to the right department." },
    { to: "/complaints/mine", title: "Track my complaints", desc: "See the status of everything you've reported." },
    { to: "/gov/schemes", title: "Government schemes", desc: "Browse active schemes and apply." },
    { to: "/services/directory", title: "Find a service provider", desc: "Search plumbers, electricians and more nearby." },
  ],
  official: [
    { to: "/complaints/villages", title: "Villages", desc: "See every village under your panchayat and drill into its complaints." },
    { to: "/gov/schemes/manage", title: "Manage schemes", desc: "Create schemes and review citizen applications." },
  ],
  provider: [
    { to: "/services/profile", title: "My provider profile", desc: "Set your service type, location and availability." },
    { to: "/services/incoming", title: "Incoming requests", desc: "See requests people have sent you and update their status." },
  ],
  farmer: [
    { to: "/agriculture/products", title: "Browse products", desc: "See what's in stock at shops near you and request what you need." },
    { to: "/agriculture/shops", title: "Shops", desc: "Browse every registered shop." },
  ],
  shop_owner: [
    { to: "/agriculture/my-shop", title: "My shop", desc: "Manage your shop and product stock." },
    { to: "/agriculture/shops", title: "All shops", desc: "See other shops on the platform." },
  ],
  asha_worker: [
    { to: "/healthcare/patients", title: "My patients", desc: "View and manage your registered patients." },
    { to: "/healthcare/patients/new", title: "Register a patient", desc: "Add a new patient to your roster." },
  ],
};

export default function Home() {
  const { user } = useAuth();
  const cards = CARDS_BY_ROLE[user?.role] || [];

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Dashboard</div>
        <h1>Welcome, {user?.full_name?.split(" ")[0]}</h1>
        <p>Here's what you can do with your {user?.role?.replace("_", " ")} account.</p>
      </div>

      {cards.map((c) => (
        <div className="card" key={c.to}>
          <div className="card-title-row">
            <h3>{c.title}</h3>
          </div>
          <p className="card-desc">{c.desc}</p>
          <div style={{ marginTop: 14 }}>
            <Link to={c.to} className="btn btn-gold btn-sm">
              Open
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}
