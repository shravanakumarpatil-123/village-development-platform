import React, { useEffect, useState } from "react";
import { api } from "../api/client";

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);

  function load() {
    api.myNotifications().then(setNotifications).catch(() => {});
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000); // poll every 30s
    return () => clearInterval(interval);
  }, []);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  async function handleOpen() {
    setOpen((o) => !o);
  }

  async function handleMarkAll() {
    try {
      await api.markAllNotificationsRead();
      load();
    } catch {
      // ignore
    }
  }

  return (
    <div style={{ position: "relative", marginBottom: 16 }}>
      <button
        className="btn btn-ghost btn-sm"
        style={{ width: "100%", justifyContent: "space-between" }}
        onClick={handleOpen}
      >
        <span>🔔 Notifications</span>
        {unreadCount > 0 && (
          <span
            style={{
              background: "var(--gold)",
              color: "#2b1c05",
              borderRadius: "999px",
              fontSize: 11,
              fontWeight: 700,
              padding: "1px 7px",
            }}
          >
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            bottom: "110%",
            left: 0,
            right: 0,
            background: "var(--surface)",
            color: "var(--ink)",
            borderRadius: 10,
            border: "1px solid var(--line)",
            boxShadow: "var(--shadow)",
            maxHeight: 320,
            overflowY: "auto",
            zIndex: 20,
            padding: 10,
          }}
        >
          {notifications.length === 0 && (
            <p className="card-meta" style={{ padding: 8 }}>Nothing yet.</p>
          )}
          {notifications.length > 0 && (
            <button className="btn btn-ghost btn-sm" style={{ width: "100%", marginBottom: 8 }} onClick={handleMarkAll}>
              Mark all as read
            </button>
          )}
          {notifications.map((n) => (
            <div
              key={n.id}
              style={{
                padding: "8px 6px",
                borderBottom: "1px solid var(--line)",
                fontSize: 13,
                fontWeight: n.is_read ? 400 : 600,
              }}
            >
              {n.message}
              <div className="card-meta" style={{ marginTop: 2 }}>
                {new Date(n.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
