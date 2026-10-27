import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import { useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppShell from "./components/AppShell";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";

import NewComplaint from "./pages/complaints/NewComplaint";
import MyComplaints from "./pages/complaints/MyComplaints";
import OfficialDashboard from "./pages/complaints/OfficialDashboard";
import VillageOverview from "./pages/complaints/VillageOverview";

import ProviderDirectory from "./pages/services/ProviderDirectory";
import ProviderProfile from "./pages/services/ProviderProfile";
import MyServiceRequests from "./pages/services/MyServiceRequests";
import IncomingRequests from "./pages/services/IncomingRequests";

import Shops from "./pages/agriculture/Shops";
import MyShop from "./pages/agriculture/MyShop";
import Products from "./pages/agriculture/Products";
import MyProductRequests from "./pages/agriculture/MyProductRequests";

import Schemes from "./pages/gov/Schemes";
import SchemeManager from "./pages/gov/SchemeManager";

import PatientList from "./pages/healthcare/PatientList";
import NewPatient from "./pages/healthcare/NewPatient";
import PatientDetail from "./pages/healthcare/PatientDetail";

const COMMUNITY_ROLES = ["citizen", "provider", "farmer", "shop_owner"];

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ padding: 40 }}>
        <p className="loading-text">Loading...</p>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/" /> : <Register />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Home />} />

        <Route path="complaints/new" element={<ProtectedRoute roles={["citizen"]}><NewComplaint /></ProtectedRoute>} />
        <Route path="complaints/mine" element={<ProtectedRoute roles={["citizen"]}><MyComplaints /></ProtectedRoute>} />
        <Route path="complaints/villages" element={<ProtectedRoute roles={["official"]}><VillageOverview /></ProtectedRoute>} />
        <Route path="complaints/dashboard" element={<ProtectedRoute roles={["official"]}><OfficialDashboard /></ProtectedRoute>} />

        <Route path="services/directory" element={<ProtectedRoute roles={COMMUNITY_ROLES}><ProviderDirectory /></ProtectedRoute>} />
        <Route path="services/profile" element={<ProtectedRoute roles={["provider"]}><ProviderProfile /></ProtectedRoute>} />
        <Route path="services/requests" element={<ProtectedRoute roles={COMMUNITY_ROLES}><MyServiceRequests /></ProtectedRoute>} />
        <Route path="services/incoming" element={<ProtectedRoute roles={["provider"]}><IncomingRequests /></ProtectedRoute>} />

        <Route path="agriculture/shops" element={<ProtectedRoute roles={COMMUNITY_ROLES}><Shops /></ProtectedRoute>} />
        <Route path="agriculture/my-shop" element={<ProtectedRoute roles={["shop_owner"]}><MyShop /></ProtectedRoute>} />
        <Route path="agriculture/products" element={<ProtectedRoute roles={COMMUNITY_ROLES}><Products /></ProtectedRoute>} />
        <Route path="agriculture/requests" element={<ProtectedRoute roles={COMMUNITY_ROLES}><MyProductRequests /></ProtectedRoute>} />

        <Route path="gov/schemes" element={<ProtectedRoute roles={COMMUNITY_ROLES}><Schemes /></ProtectedRoute>} />
        <Route path="gov/schemes/manage" element={<ProtectedRoute roles={["official"]}><SchemeManager /></ProtectedRoute>} />

        <Route path="healthcare/patients" element={<ProtectedRoute roles={["asha_worker"]}><PatientList /></ProtectedRoute>} />
        <Route path="healthcare/patients/new" element={<ProtectedRoute roles={["asha_worker"]}><NewPatient /></ProtectedRoute>} />
        <Route path="healthcare/patients/:patientId" element={<ProtectedRoute roles={["asha_worker"]}><PatientDetail /></ProtectedRoute>} />
      </Route>

      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}
