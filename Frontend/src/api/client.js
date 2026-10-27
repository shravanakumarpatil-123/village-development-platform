/*
 * One place that talks to the FastAPI backend.
 * Reads the token from localStorage and attaches it to every request
 * automatically, so individual pages never have to think about auth headers.
 */
const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Turns a relative path like "/uploads/complaints/x.jpg" (from the backend)
// into a full URL an <img> tag can load.
export function fileUrl(path) {
  if (!path) return null;
  return path.startsWith("http") ? path : `${BASE_URL}${path}`;
}

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: form ? form : body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  const text = await res.text();
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    const message =
      (data && (data.detail?.[0]?.msg || data.detail)) ||
      `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : "Something went wrong");
  }

  return data;
}

export const api = {
  // ---- Auth ----
  register: (payload) => request("/auth/register", { method: "POST", body: payload, auth: false }),
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append("grant_type", "password");
    form.append("username", email);
    form.append("password", password);
    return request("/auth/login", { method: "POST", form, auth: false });
  },
  me: () => request("/auth/me"),

  // ---- Complaints (community) ----
  createComplaint: (payload) => request("/complaints/", { method: "POST", body: payload }),
  uploadComplaintPhoto: (id, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/complaints/${id}/photo`, { method: "POST", form });
  },
  myComplaints: () => request("/complaints/mine"),
  allComplaints: (village) =>
    request(`/complaints/${village ? `?village=${encodeURIComponent(village)}` : ""}`),
  listComplaintVillages: () => request("/complaints/villages/list"),
  villageSummary: () => request("/complaints/villages/summary"),
  updateComplaintStatus: (id, status) =>
    request(`/complaints/${id}/status`, { method: "PATCH", body: { status } }),
  complaintComments: (id) => request(`/complaints/${id}/comments`),
  addComplaintComment: (id, message) =>
    request(`/complaints/${id}/comments`, { method: "POST", body: { message } }),
  myNotifications: () => request("/complaints/notifications/mine"),
  markNotificationRead: (id) =>
    request(`/complaints/notifications/${id}/read`, { method: "PATCH" }),
  markAllNotificationsRead: () =>
    request("/complaints/notifications/read-all", { method: "PATCH" }),

  // ---- Services (personal) ----
  searchProviders: (params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v != null))
    ).toString();
    return request(`/services/providers${qs ? `?${qs}` : ""}`, { auth: false });
  },
  becomeProvider: (payload) => request("/services/providers", { method: "POST", body: payload }),
  myProviderProfile: () => request("/services/providers/mine"),
  updateMyProviderProfile: (payload) =>
    request("/services/providers/mine", { method: "PATCH", body: payload }),
  requestService: (payload) => request("/services/requests", { method: "POST", body: payload }),
  myServiceRequests: () => request("/services/requests/mine"),
  incomingServiceRequests: () => request("/services/requests/incoming"),
  updateServiceRequestStatus: (id, status) =>
    request(`/services/requests/${id}/status`, { method: "PATCH", body: { status } }),
  leaveReview: (payload) => request("/services/reviews", { method: "POST", body: payload }),
  providerReviews: (providerId) => request(`/services/providers/${providerId}/reviews`, { auth: false }),

  // ---- Agriculture ----
  listShops: () => request("/agriculture/shops", { auth: false }),
  createShop: (payload) => request("/agriculture/shops", { method: "POST", body: payload }),
  updateMyShop: (payload) => request("/agriculture/shops/mine", { method: "PATCH", body: payload }),
  listProducts: () => request("/agriculture/products", { auth: false }),
  addProduct: (shopId, payload) =>
    request(`/agriculture/shops/${shopId}/products`, { method: "POST", body: payload }),
  updateProduct: (productId, payload) =>
    request(`/agriculture/products/${productId}`, { method: "PATCH", body: payload }),
  myLowStockProducts: () => request("/agriculture/shops/mine/low-stock"),
  requestProduct: (payload) => request("/agriculture/requests", { method: "POST", body: payload }),
  requestProductsBatch: (items) =>
    request("/agriculture/requests/batch", { method: "POST", body: { items } }),
  myProductRequests: () => request("/agriculture/requests/mine"),
  myShopIncomingRequests: () => request("/agriculture/shops/mine/requests"),
  updateProductRequestStatus: (id, status) =>
    request(`/agriculture/requests/${id}/status`, { method: "PATCH", body: { status } }),

  // ---- Government: schemes ----
  createScheme: (payload) => request("/gov/schemes", { method: "POST", body: payload }),
  listSchemes: (includeInactive) =>
    request(`/gov/schemes${includeInactive ? "?include_inactive=true" : ""}`),
  updateScheme: (id, payload) => request(`/gov/schemes/${id}`, { method: "PATCH", body: payload }),
  applyToScheme: (schemeId, note) =>
    request(`/gov/schemes/${schemeId}/apply`, { method: "POST", body: { note } }),
  mySchemeApplications: () => request("/gov/schemes/applications/mine"),
  allSchemeApplications: (schemeId) =>
    request(`/gov/schemes/applications${schemeId ? `?scheme_id=${schemeId}` : ""}`),
  updateSchemeApplicationStatus: (id, status) =>
    request(`/gov/schemes/applications/${id}/status`, { method: "PATCH", body: { status } }),

  // ---- Healthcare: AppAyu V1 ----
  registerPatient: (payload) => request("/healthcare/patients", { method: "POST", body: payload }),
  listPatients: (village) =>
    request(`/healthcare/patients${village ? `?village=${encodeURIComponent(village)}` : ""}`),
  getPatient: (id) => request(`/healthcare/patients/${id}`),
  updatePatient: (id, payload) => request(`/healthcare/patients/${id}`, { method: "PATCH", body: payload }),
  addMedicalHistory: (patientId, payload) =>
    request(`/healthcare/patients/${patientId}/medical-history`, { method: "POST", body: payload }),
  listMedicalHistory: (patientId) => request(`/healthcare/patients/${patientId}/medical-history`),
  uploadScreening: (patientId, file, screeningType = "skin") => {
    const form = new FormData();
    form.append("file", file);
    return request(`/healthcare/patients/${patientId}/screenings?screening_type=${screeningType}`, {
      method: "POST",
      form,
    });
  },
  listPatientScreenings: (patientId) => request(`/healthcare/patients/${patientId}/screenings`),
};
