import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import NotificationBell from "./NotificationBell";

const NAV_BY_ROLE = {
  citizen: [
    { to: "/complaints/new", label: "File a complaint" },
    { to: "/complaints/mine", label: "My complaints" },
    { to: "/services/requests", label: "My service requests" },
    { to: "/agriculture/requests", label: "My product requests" },
  ],
  official: [
    { to: "/complaints/villages", label: "Villages" },
    { to: "/gov/schemes/manage", label: "Manage schemes" },
  ],
  provider: [
    { to: "/services/directory", label: "Provider directory" },
    { to: "/services/profile", label: "My provider profile" },
    { to: "/services/incoming", label: "Incoming requests" },
  ],
  farmer: [
    { to: "/agriculture/products", label: "Browse products" },
    { to: "/agriculture/shops", label: "Shops" },
    { to: "/agriculture/requests", label: "My requests" },
  ],
  shop_owner: [
    { to: "/agriculture/my-shop", label: "My shop" },
    { to: "/agriculture/shops", label: "All shops" },
  ],
  asha_worker: [
    { to: "/healthcare/patients", label: "My patients" },
    { to: "/healthcare/patients/new", label: "Register patient" },
  ],
};

const COMMON_NAV = [
  { to: "/services/directory", label: "Find a service" },
  { to: "/gov/schemes", label: "Schemes" },
];

export default function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const roleNav = NAV_BY_ROLE[user?.role] || [];
  const isOfficial = user?.role === "official";
  const isAshaWorker = user?.role === "asha_worker";

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand">Gram Setu</div>
          <div className="brand-sub">Village Development Platform</div>
        </div>

        <nav>
          <div className="nav-group">
            <div className="nav-label">
              {isAshaWorker ? "Healthcare · AppAyu" : "Your modules"}
            </div>
            {roleNav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
              >
                {item.label}
              </NavLink>
            ))}
          </div>

          {!isOfficial && !isAshaWorker && (
            <div className="nav-group">
              <div className="nav-label">Community</div>
              {COMMON_NAV.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
                >
                  {item.label}
                </NavLink>
              ))}
              <NavLink
                to="/agriculture/shops"
                className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
              >
                Local shops
              </NavLink>
            </div>
          )}
        </nav>

        <div className="sidebar-footer">
          <NotificationBell />
          <div className="sidebar-user">
            {user?.full_name}
            {user?.asha_id && (
              <div style={{ fontSize: 11, color: "var(--green)", fontWeight: 600, marginTop: 2 }}>
                🆔 {user.asha_id}
              </div>
            )}
            <br />
            <span className="role-tag">{user?.role?.replace("_", " ")}</span>
          </div>
          <button className="btn btn-ghost btn-sm" style={{ width: "100%" }} onClick={handleLogout}>
            Log out
          </button>
        </div>
      </aside>

      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
