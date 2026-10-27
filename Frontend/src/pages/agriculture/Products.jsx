import React, { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { api } from "../../api/client";

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const shopFilter = searchParams.get("shop");

  const [products, setProducts] = useState(null);
  const [shops, setShops] = useState([]);
  const [error, setError] = useState("");
  const [cart, setCart] = useState({}); // { productId: quantity }
  const [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Promise.all([api.listProducts(), api.listShops()])
      .then(([p, s]) => {
        setProducts(p);
        setShops(s);
      })
      .catch((err) => setError(err.message));
  }, []);

  function setQuantity(productId, quantity) {
    setCart((c) => {
      const next = { ...c };
      const n = parseInt(quantity, 10);
      if (!n || n <= 0) {
        delete next[productId];
      } else {
        next[productId] = n;
      }
      return next;
    });
  }

  const cartItems = Object.entries(cart).filter(([, qty]) => qty > 0);
  const cartCount = cartItems.length;

  async function handleSubmitCart() {
    setError("");
    setBusy(true);
    try {
      const items = cartItems.map(([product_id, quantity]) => ({
        product_id: Number(product_id),
        quantity,
      }));
      if (items.length === 1) {
        await api.requestProduct(items[0]);
      } else {
        await api.requestProductsBatch(items);
      }
      setCart({});
      setSubmitted(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const shopById = Object.fromEntries(shops.map((s) => [s.id, s]));
  const visibleProducts = shopFilter
    ? products?.filter((p) => String(p.shop_id) === shopFilter)
    : products;
  const filterShop = shopFilter ? shopById[shopFilter] : null;

  return (
    <div>
      <div className="page-header">
        <div className="eyebrow">Agriculture · Module 3</div>
        <h1>Browse products</h1>
        <p>Add quantities for whatever you need, then send one request for everything.</p>
      </div>

      {shopFilter && (
        <div style={{ marginBottom: 18, display: "flex", alignItems: "center", gap: 10 }}>
          <span className="dept-tag">
            Showing: {filterShop ? filterShop.name : `Shop #${shopFilter}`}
          </span>
          <button className="btn btn-ghost btn-sm" onClick={() => setSearchParams({})}>
            Show all shops
          </button>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}
      {submitted && <div className="success-banner">Request sent — check "My requests" for status.</div>}
      {!products && !error && <p className="loading-text">Loading...</p>}

      {products && visibleProducts?.length === 0 && (
        <div className="empty-state">
          <h3>No products listed yet</h3>
          <p>
            {shopFilter
              ? "This shop hasn't added any products yet."
              : "Check back once shops have added stock."}
          </p>
        </div>
      )}

      {visibleProducts?.map((p) => (
        <div className="card" key={p.id}>
          <div className="card-title-row">
            <h3>{p.name}</h3>
            <span className="card-meta">₹{p.price}</span>
          </div>
          <p className="card-meta">
            {p.stock} in stock ·{" "}
            {shopById[p.shop_id] ? (
              <Link to={`/agriculture/products?shop=${p.shop_id}`}>{shopById[p.shop_id].name}</Link>
            ) : (
              `Shop #${p.shop_id}`
            )}
          </p>

          <div style={{ marginTop: 14, maxWidth: 160 }}>
            <input
              type="number"
              min="0"
              max={p.stock}
              placeholder="Qty"
              value={cart[p.id] || ""}
              onChange={(e) => setQuantity(p.id, e.target.value)}
            />
          </div>
        </div>
      ))}

      {cartCount > 0 && (
        <div
          style={{
            position: "sticky",
            bottom: 20,
            marginTop: 20,
            background: "var(--surface)",
            border: "1px solid var(--line)",
            borderRadius: 10,
            padding: 16,
            boxShadow: "var(--shadow)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span className="card-meta">
            {cartCount} product{cartCount > 1 ? "s" : ""} selected
          </span>
          <button className="btn btn-gold" onClick={handleSubmitCart} disabled={busy}>
            {busy ? "Sending..." : `Send request${cartCount > 1 ? " for all" : ""}`}
          </button>
        </div>
      )}
    </div>
  );
}
