// --- Auth token helpers ---
// NOTE: localStorage is fine here — this is a real deployed web app, not a
// Claude artifact sandbox. It's the standard place for a JWT in a simple SPA-ish setup.

function getToken() {
  return localStorage.getItem('token');
}

function setSession(token, role) {
  localStorage.setItem('token', token);
  localStorage.setItem('role', role);
}

function getRole() {
  return localStorage.getItem('role');
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
}

// --- API fetch wrapper ---
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = options.headers || {};
  headers['Content-Type'] = 'application/json';
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(path, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

// --- Cart helpers (stored client-side until order is placed) ---
function getCart() {
  return JSON.parse(localStorage.getItem('cart') || '{"restaurant_id": null, "items": []}');
}

function setCart(cart) {
  localStorage.setItem('cart', JSON.stringify(cart));
}

function clearCart() {
  localStorage.removeItem('cart');
}

function addToCart(restaurantId, menuItemId, name, price) {
  let cart = getCart();

  if (cart.restaurant_id && cart.restaurant_id !== restaurantId) {
    if (!confirm('Your cart has items from another restaurant. Clear it and start a new cart?')) {
      return;
    }
    cart = { restaurant_id: null, items: [] };
  }

  cart.restaurant_id = restaurantId;
  const existing = cart.items.find(i => i.menu_item_id === menuItemId);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.items.push({ menu_item_id: menuItemId, name, price, quantity: 1 });
  }
  setCart(cart);
  alert(`${name} added to cart`);
}
