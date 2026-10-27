import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import StatusBadge from "../../components/StatusBadge";

export default function MyShop() {
  const { user } = useAuth();
  const [shops, setShops] = useState(null);
  const [myShop, setMyShop] = useState(null);
  const [shopForm, setShopForm] = useState({ name: "", location: "" });
  const [editingShop, setEditingShop] = useState(false);
  const [productForm, setProductForm] = useState({ name: "", price: "", stock: "", low_stock_threshold: "5" });
  const [products, setProducts] = useState([]);
  const [editingProductId, setEditingProductId] = useState(null);
  const [editProductForm, setEditProductForm] = useState({ name: "", price: "", stock: "" });
  const [lowStock, setLowStock] = useState([]);
  const [incoming, setIncoming] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [savingReqId, setSavingReqId] = useState(null);

  function loadEverything() {
    Promise.all([api.listShops(), api.listProducts()])
      .then(([allShops, allProducts]) => {
        setShops(allShops);
        setProducts(allProducts);
        const existing = allShops.find((s) => s.owner_id === user.id);
        if (existing) {
          setMyShop(existing);
          setShopForm({ name: existing.name, location: existing.location || "" });
        }
      })
      .catch((err) => setError(err.message));
  }

  function loadIncoming() {
    api.myShopIncomingRequests().then(setIncoming).catch(() => setIncoming([]));
  }

  function loadLowStock() {
    api.myLowStockProducts().then(setLowStock).catch(() => setLowStock([]));
  }

  useEffect(() => {
    loadEverything();
    loadIncoming();
    loadLowStock();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleCreateShop(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const shop = await api.createShop(shopForm);
      setMyShop(shop);
      loadEverything();
    } catch (err) {
      setError(err.message || "Could not create shop");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpdateShop(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const updated = await api.updateMyShop(shopForm);
      setMyShop(updated);
      setEditingShop(false);
    } catch (err) {
      setError(err.message || "Could not update shop");
    } finally {
      setBusy(false);
    }
  }

  async function handleAddProduct(e) {
    e.preventDefault();
    if (!myShop) return;
    setError("");
    setBusy(true);
    try {
      await api.addProduct(myShop.id, {
        name: productForm.name,
        price: parseFloat(productForm.price),
        stock: parseInt(productForm.stock || "0", 10),
        low_stock_threshold: parseInt(productForm.low_stock_threshold || "5", 10),
      });
      setProductForm({ name: "", price: "", stock: "", low_stock_threshold: "5" });
      loadEverything();
      loadLowStock();
    } catch (err) {
      setError(err.message || "Could not add product");
    } finally {
      setBusy(false);
    }
  }

  function startEditProduct(p) {
    setEditingProductId(p.id);
    setEditProductForm({ name: p.name, price: String(p.price), stock: String(p.stock) });
  }

  async function handleSaveProduct(id) {
    setError("");
    setBusy(true);
    try {
      await api.updateProduct(id, {
        name: editProductForm.name,
        price: parseFloat(editProductForm.price),
        stock: parseInt(editProductForm.stock, 10),
      });
      setEditingProductId(null);
      loadEverything();
      loadLowStock();
    } catch (err) {
      setError(err.message || "Could not update product");
    } finally {
      setBusy(false);
    }
  }

  const myProducts = myShop ? products.filter((p) => p.shop_id === myShop.id) : [];

  async function handleRequestStatus(id, status) {
    setSavingReqId(id);
    try {
      await api.updateProductRequestStatus(id, status);
      loadIncoming();
      loadEverything();
      loadLowStock();
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingReqId(null);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Agriculture · Module 3</div>
        <h1>My shop</h1>
        <p>Register your shop once, then add products for farmers to request.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {!myShop && (
        <div className="card form-card">
          <h3 style={{ marginBottom: 14 }}>Register your shop</h3>
          <form onSubmit={handleCreateShop}>
            <div className="field">
              <label htmlFor="name">Shop name</label>
              <input
                id="name"
                required
                value={shopForm.name}
                onChange={(e) => setShopForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Krishna Agro Center"
              />
            </div>
            <div className="field">
              <label htmlFor="location">Location</label>
              <input
                id="location"
                value={shopForm.location}
                onChange={(e) => setShopForm((f) => ({ ...f, location: e.target.value }))}
                placeholder="Near the bus stand"
              />
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {busy ? "Creating..." : "Create shop"}
            </button>
          </form>
        </div>
      )}

      {myShop && (
        <>
          <div className="card">
            {!editingShop ? (
              <>
                <div className="card-title-row">
                  <h3>{myShop.name}</h3>
                  <button className="btn btn-ghost btn-sm" onClick={() => setEditingShop(true)}>
                    Edit
                  </button>
                </div>
                {myShop.location && <p className="card-meta">📍 {myShop.location}</p>}
              </>
            ) : (
              <form onSubmit={handleUpdateShop}>
                <div className="field">
                  <label>Shop name</label>
                  <input
                    required
                    value={shopForm.name}
                    onChange={(e) => setShopForm((f) => ({ ...f, name: e.target.value }))}
                  />
                </div>
                <div className="field">
                  <label>Location</label>
                  <input
                    value={shopForm.location}
                    onChange={(e) => setShopForm((f) => ({ ...f, location: e.target.value }))}
                  />
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-gold btn-sm" type="submit" disabled={busy}>
                    Save
                  </button>
                  <button className="btn btn-ghost btn-sm" type="button" onClick={() => setEditingShop(false)}>
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>

          {lowStock.length > 0 && (
            <div className="error-banner" style={{ marginTop: 20 }}>
              ⚠️ Low stock: {lowStock.map((p) => `${p.name} (${p.stock} left)`).join(", ")}
            </div>
          )}

          <div className="card form-card" style={{ marginTop: 20 }}>
            <h3 style={{ marginBottom: 14 }}>Add a product</h3>
            <form onSubmit={handleAddProduct}>
              <div className="field">
                <label htmlFor="pname">Product name</label>
                <input
                  id="pname"
                  required
                  value={productForm.name}
                  onChange={(e) => setProductForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="Urea fertilizer (50kg)"
                />
              </div>
              <div className="two-col">
                <div className="field">
                  <label htmlFor="price">Price</label>
                  <input
                    id="price"
                    type="number"
                    step="0.01"
                    required
                    value={productForm.price}
                    onChange={(e) => setProductForm((f) => ({ ...f, price: e.target.value }))}
                    placeholder="450"
                  />
                </div>
                <div className="field">
                  <label htmlFor="stock">Stock</label>
                  <input
                    id="stock"
                    type="number"
                    value={productForm.stock}
                    onChange={(e) => setProductForm((f) => ({ ...f, stock: e.target.value }))}
                    placeholder="100"
                  />
                </div>
              </div>
              <div className="field">
                <label htmlFor="threshold">Low stock alert threshold</label>
                <input
                  id="threshold"
                  type="number"
                  value={productForm.low_stock_threshold}
                  onChange={(e) => setProductForm((f) => ({ ...f, low_stock_threshold: e.target.value }))}
                />
                <p className="hint">You'll see a warning here once stock drops to this level or below.</p>
              </div>
              <button className="btn btn-gold" type="submit" disabled={busy}>
                {busy ? "Adding..." : "Add product"}
              </button>
            </form>
          </div>

          <h3 style={{ marginTop: 26, marginBottom: 12 }}>Your products</h3>
          {myProducts.length === 0 && (
            <div className="empty-state">
              <h3>No products yet</h3>
              <p>Add your first product above.</p>
            </div>
          )}
          {myProducts.map((p) =>
            editingProductId === p.id ? (
              <div className="card" key={p.id}>
                <div className="two-col">
                  <div className="field">
                    <label>Name</label>
                    <input
                      value={editProductForm.name}
                      onChange={(e) => setEditProductForm((f) => ({ ...f, name: e.target.value }))}
                    />
                  </div>
                  <div className="field">
                    <label>Price</label>
                    <input
                      type="number"
                      step="0.01"
                      value={editProductForm.price}
                      onChange={(e) => setEditProductForm((f) => ({ ...f, price: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="field">
                  <label>Stock</label>
                  <input
                    type="number"
                    value={editProductForm.stock}
                    onChange={(e) => setEditProductForm((f) => ({ ...f, stock: e.target.value }))}
                  />
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-gold btn-sm" onClick={() => handleSaveProduct(p.id)} disabled={busy}>
                    Save
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setEditingProductId(null)}>
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="list-row" key={p.id}>
                <span>
                  {p.name} {p.is_low_stock && <span className="badge badge-rejected">low stock</span>}
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className="card-meta">₹{p.price} · {p.stock} in stock</span>
                  <button className="btn btn-ghost btn-sm" onClick={() => startEditProduct(p)}>
                    Edit
                  </button>
                </span>
              </div>
            )
          )}

          <h3 style={{ marginTop: 26, marginBottom: 12 }}>Incoming requests</h3>
          {incoming === null && <p className="loading-text">Loading...</p>}
          {incoming && incoming.length === 0 && (
            <div className="empty-state">
              <h3>No requests yet</h3>
              <p>When a farmer requests one of your products, it'll show up here.</p>
            </div>
          )}
          {incoming?.map((r) => (
            <div className="card" key={r.id}>
              <div className="card-title-row">
                <h3>Product #{r.product_id} · Qty {r.quantity}</h3>
                <StatusBadge status={r.status} />
              </div>
              <p className="card-meta">
                Requested {new Date(r.created_at).toLocaleDateString()}
                {r.batch_id && " · part of a multi-item order"}
              </p>
              {r.status === "pending" && (
                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                  <button
                    className="btn btn-gold btn-sm"
                    disabled={savingReqId === r.id}
                    onClick={() => handleRequestStatus(r.id, "approved")}
                  >
                    Approve
                  </button>
                  <button
                    className="btn btn-ghost btn-sm"
                    disabled={savingReqId === r.id}
                    onClick={() => handleRequestStatus(r.id, "rejected")}
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
