'use strict';
(() => {
  const catalog = window.AYLIN_CATALOG;
  const products = catalog.products;
  const byId = new Map(products.map(product => [product.id, product]));
  const CART_KEY = 'aylin-shop-demo-cart-v1';
  const ORDERS_KEY = 'aylin-shop-demo-orders-v1';
  const money = value => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(value / 100);
  const $ = selector => document.querySelector(selector);
  let toastTimer;
  let activeCategory = 'todos';
  let submitting = false;
  let memoryOnly = false;

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }
  function storageWarning() {
    memoryOnly = true;
    $('#storage-warning').hidden = false;
    $('#storage-warning').textContent = 'El navegador no permite guardar algunos datos. Puedes probar la compra, pero esos datos solo se conservarán mientras esta página permanezca abierta.';
  }
  function readStorage(type, key, fallback) {
    try {
      const raw = window[type].getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch { storageWarning(); return fallback; }
  }
  function writeStorage(type, key, value) {
    try { window[type].setItem(key, JSON.stringify(value)); }
    catch { storageWarning(); }
  }
  function sanitizeCart(raw) {
    const clean = {};
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return clean;
    for (const product of products) {
      const quantity = raw[product.id];
      if (Number.isInteger(quantity) && quantity > 0 && product.stockQuantity > 0) {
        clean[product.id] = Math.min(quantity, product.stockQuantity);
      }
    }
    return clean;
  }
  let cart = sanitizeCart(readStorage('localStorage', CART_KEY, {}));
  const customerFields = ['name', 'email', 'phone', 'address', 'postal', 'city', 'province'];
  const loadedOrders = readStorage('sessionStorage', ORDERS_KEY, []);
  // La sesión no es una fuente fiable: descarta datos manipulados o incompletos.
  let orders = Array.isArray(loadedOrders) ? loadedOrders.filter(order => {
    return order && order.demo === true && typeof order.id === 'string' && /^DEMO-[a-zA-Z0-9-]{8,100}$/.test(order.id)
      && typeof order.date === 'string' && Number.isFinite(Date.parse(order.date))
      && order.customer && customerFields.every(field => typeof order.customer[field] === 'string' && order.customer[field].length <= 180)
      && Array.isArray(order.items) && order.items.length > 0 && order.items.length <= products.length
      && order.items.every(item => item && byId.has(item.id) && Number.isInteger(item.quantity) && item.quantity > 0 && item.quantity <= byId.get(item.id).stockQuantity);
  }).slice(0, 20).map(order => ({
    id: order.id, date: order.date, demo: true, status: 'Confirmado · demo sin pago', totalMinor: 0,
    customer: Object.fromEntries(customerFields.map(field => [field, order.customer[field]])),
    items: order.items.map(item => ({ id: item.id, quantity: item.quantity }))
  })) : [];
  function lines() {
    return products.filter(product => cart[product.id]).map(product => ({ product, quantity: cart[product.id] }));
  }
  function announce(text) {
    clearTimeout(toastTimer);
    $('#toast').textContent = text;
    toastTimer = setTimeout(() => { $('#toast').textContent = ''; }, 4500);
  }
  function setCategory(category) {
    activeCategory = category === 'todos' || catalog.categories[category] ? category : 'todos';
    document.querySelectorAll('[data-filter]').forEach(button => {
      const selected = button.dataset.filter === activeCategory;
      button.classList.toggle('active', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
    document.querySelectorAll('.product-card').forEach(card => {
      card.hidden = activeCategory !== 'todos' && card.dataset.category !== activeCategory;
    });
    const count = products.filter(product => activeCategory === 'todos' || product.category === activeCategory).length;
    $('#filter-status').textContent = `${count} productos: ${catalog.categories[activeCategory] || 'Todos los productos'}`;
  }
  function renderProducts() {
    products.forEach(product => {
      const card = node('article', undefined, 'product-card');
      card.dataset.category = product.category;
      card.dataset.productId = product.id;
      const photo = node('div', undefined, 'product-photo');
      const image = node('img');
      image.src = product.image; image.alt = product.alt;
      image.width = product.width; image.height = product.height; image.loading = 'lazy';
      const available = product.stockQuantity > 0;
      photo.append(image, node('span', available ? 'En stock · demo' : 'Sin stock · demo', 'stock'));
      const heading = node('div', undefined, 'product-title-row');
      heading.append(node('h3', product.name), node('span', money(product.priceMinor), 'product-price'));
      const add = node('button', 'Añadir al carrito +', 'button');
      add.type = 'button'; add.disabled = !available;
      add.setAttribute('aria-label', `Añadir ${product.name} al carrito`);
      add.addEventListener('click', () => {
        if ((cart[product.id] || 0) >= product.stockQuantity) {
          announce(`Has alcanzado el límite de ${product.stockQuantity} unidades de prueba.`); return;
        }
        cart[product.id] = (cart[product.id] || 0) + 1;
        changedCart(); announce(`${product.name} añadido al carrito.`);
      });
      card.append(photo, node('p', catalog.categories[product.category], 'product-tag'), heading, node('p', product.description, 'product-description'), add);
      $('#products').append(card);
      const li = node('li'); const credit = node('a', `${product.name} — ${product.author} / Pexels`);
      credit.href = product.source; credit.target = '_blank'; credit.rel = 'noopener noreferrer';
      li.append(credit); $('#photo-credits').append(li);
    });
  }
  function changedCart() {
    cart = sanitizeCart(cart);
    writeStorage('localStorage', CART_KEY, cart);
    $('#checkout-error').textContent = '';
    renderCart();
  }
  function quantityButton(product, change, text) {
    const button = node('button', text);
    button.type = 'button'; button.dataset.quantityFor = product.id; button.dataset.change = change;
    button.setAttribute('aria-label', `${change > 0 ? 'Aumentar' : 'Reducir'} cantidad de ${product.name}`);
    button.disabled = change > 0 && cart[product.id] >= product.stockQuantity;
    button.addEventListener('click', () => {
      const next = (cart[product.id] || 0) + change;
      if (next <= 0) delete cart[product.id]; else cart[product.id] = Math.min(next, product.stockQuantity);
      changedCart();
      const replacement = document.querySelector(`[data-quantity-for="${product.id}"][data-change="${change}"]`);
      if (replacement && !replacement.disabled) replacement.focus();
      else if (next > 0) document.querySelector(`[data-quantity-for="${product.id}"][data-change="-1"]`)?.focus();
      else $('#cart-clear').hidden ? $('#cart-total').focus() : $('#cart-clear').focus();
      announce(next <= 0 ? `${product.name} eliminado.` : `${product.name}: ${cart[product.id]} unidades.`);
    });
    return button;
  }
  function renderCart() {
    const items = lines();
    const count = items.reduce((sum, item) => sum + item.quantity, 0);
    $('#cart-count').textContent = count;
    $('#cart-count').setAttribute('aria-label', `${count} unidades en el carrito`);
    const list = $('#cart-items'); list.replaceChildren();
    if (!items.length) {
      list.append(node('p', 'Tu próxima selección empieza aquí.', 'empty-cart'), node('p', 'Añade alguno de los seis productos para probar la compra.', 'empty-note'));
    }
    for (const { product, quantity } of items) {
      const row = node('article', undefined, 'cart-line'); row.dataset.cartId = product.id;
      const image = node('img'); image.src = product.image; image.alt = ''; image.width = 70; image.height = 85;
      const info = node('div'); info.append(node('h3', product.name), node('span', `${money(product.priceMinor)} / unidad`, 'line-price'));
      const counter = node('div', undefined, 'quantity');
      const output = node('output', quantity); output.setAttribute('aria-label', `Cantidad de ${product.name}`);
      counter.append(quantityButton(product, -1, '−'), output, quantityButton(product, 1, '+')); info.append(counter);
      const remove = node('button', 'Eliminar', 'remove-button'); remove.type = 'button';
      remove.setAttribute('aria-label', `Eliminar ${product.name} del carrito`);
      remove.addEventListener('click', () => {
        delete cart[product.id]; changedCart(); $('#cart-total').focus(); announce(`${product.name} eliminado del carrito.`);
      });
      row.append(image, info, remove); list.append(row);
    }
    $('#cart-total').textContent = money(0); $('#cart-total').tabIndex = -1;
    $('#checkout-start').disabled = !items.length;
    $('#cart-clear').hidden = !items.length;
    $('#submit-order').disabled = !items.length;
    if (!items.length) $('#checkout').hidden = true;
    $('#checkout-summary').replaceChildren();
    for (const { product, quantity } of items) {
      const row = node('div', undefined, 'summary-line'); row.append(node('span', `${product.name} × ${quantity}`), node('span', money(0))); $('#checkout-summary').append(row);
    }
    $('#checkout-summary').append(node('p', 'Envío de prueba: 0,00 €', 'fine-print'));
  }
  function itemList(order) {
    const list = node('ul');
    order.items.forEach(item => list.append(node('li', `${byId.get(item.id).name} × ${item.quantity} — ${money(0)}`)));
    return list;
  }
  function shippingText(customer) {
    return `${customer.name}\n${customer.address}\n${customer.postal} · ${customer.city}, ${customer.province}\n${customer.email}\n${customer.phone}`;
  }
  function simulatedNotice(order, target) {
    const box = node('div', undefined, 'sim-notification');
    box.append(node('strong', `${target === 'merchant' ? 'Aviso para Aylin' : 'Confirmación para el comprador'} · SIMULADO, NO ENVIADO`));
    box.append(node('p', target === 'merchant' ? 'Destino comercial: pendiente de configurar.' : `Destino de ejemplo: ${order.customer.email}`));
    box.append(node('p', `Pedido ${order.id}`, 'order-id'), itemList(order), node('p', `Total: ${money(0)} · Estado: ${order.status}`), node('p', 'Datos ficticios de envío:'), node('address', shippingText(order.customer)));
    return box;
  }
  function renderOrders() {
    const target = $('#orders'); target.replaceChildren();
    $('#clear-history').hidden = !orders.length;
    if (!orders.length) target.append(node('p', 'Todavía no hay pedidos de prueba en esta pestaña.', 'empty-note'));
    for (const order of orders) {
      const record = node('details', undefined, 'order-record');
      const summary = node('summary');
      const date = new Intl.DateTimeFormat('es-ES', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(order.date));
      summary.append(node('span', 'Pedido gratuito de prueba'), node('small', `${date} · ${money(0)} · Ver detalle`));
      const content = node('div', undefined, 'order-content');
      content.append(node('p', order.id, 'order-id'), node('p', `Estado: ${order.status}`, 'fine-print'), itemList(order), node('p', `Total de demostración: ${money(0)}`), node('h3', 'Datos ficticios del pedido'), node('address', shippingText(order.customer)), node('h3', 'Notificaciones simuladas'), node('p', 'No se han enviado correos. Estos son los avisos que se prepararían para una integración futura.', 'fine-print'), simulatedNotice(order, 'merchant'), simulatedNotice(order, 'buyer'));
      record.append(summary, content); target.append(record);
    }
  }
  $('#checkout-start').addEventListener('click', () => {
    if (!lines().length) return;
    $('#confirmation').hidden = true; $('#checkout').hidden = false;
    $('#checkout-title').focus(); $('#checkout').scrollIntoView({ block: 'start' });
  });
  $('#cart-clear').addEventListener('click', () => { cart = {}; changedCart(); $('#cart-total').focus(); announce('Carrito vaciado.'); });
  $('#fill-demo').addEventListener('click', () => {
    const sample = { name: 'Alex Demo', email: 'ejemplo@example.com', phone: '600000000', address: 'Calle de Ejemplo, 1', postal: '28001', city: 'Ciudad de ejemplo', province: 'Provincia de ejemplo' };
    for (const [key, value] of Object.entries(sample)) $('#checkout-form').elements.namedItem(key).value = value;
    announce('Datos ficticios rellenados. Revisa la confirmación de demostración antes de continuar.');
  });
  $('#checkout-form').addEventListener('submit', event => {
    event.preventDefault();
    if (submitting || !event.currentTarget.reportValidity()) return;
    const selected = lines();
    if (!selected.length) { $('#checkout-error').textContent = 'El carrito está vacío. Añade un producto antes de continuar.'; return; }
    if (selected.some(({ product, quantity }) => product.priceMinor !== 0 || product.stockQuantity < quantity) || window.AYLIN_PAYMENTS.mode !== 'demo') {
      $('#checkout-error').textContent = 'Solo se permiten productos gratuitos y disponibles en esta demostración.'; return;
    }
    const data = new FormData(event.currentTarget);
    const customer = Object.fromEntries(customerFields.map(field => [field, String(data.get(field) || '').trim()]));
    if (Object.values(customer).some(value => !value) || customer.name.length < 3 || customer.address.length < 5 || customer.city.length < 2 || customer.province.length < 2) {
      $('#checkout-error').textContent = 'Completa todos los campos con datos ficticios válidos, sin dejar solo espacios.'; return;
    }
    if (data.get('demoConsent') !== 'on' || data.get('payment') !== 'demo') {
      $('#checkout-error').textContent = 'Confirma que utilizas datos ficticios y el pedido gratuito de demostración.'; return;
    }
    submitting = true; $('#submit-order').disabled = true;
    const unique = globalThis.crypto?.randomUUID?.() || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
    const order = { id: `DEMO-${unique}`, date: new Date().toISOString(), demo: true, status: 'Confirmado · demo sin pago', totalMinor: 0, customer, items: selected.map(({ product, quantity }) => ({ id: product.id, quantity })) };
    orders = [order, ...orders].slice(0, 20);
    writeStorage('sessionStorage', ORDERS_KEY, orders); renderOrders();
    cart = {}; changedCart();
    event.currentTarget.reset();
    $('#confirmation-message').textContent = `Pedido ${order.id} · Total: ${money(0)}. ${memoryOnly ? 'Guardado temporalmente en memoria.' : 'Guardado en el historial de esta pestaña.'}`;
    $('#confirmation').hidden = false; $('#confirmation-title').focus(); $('#confirmation').scrollIntoView({ block: 'start' });
    announce('Pedido de demostración creado. No hay cobros ni correos enviados.');
    submitting = false;
  });
  $('#clear-history').addEventListener('click', () => {
    orders = [];
    try { sessionStorage.removeItem(ORDERS_KEY); } catch { storageWarning(); }
    renderOrders(); $('#confirmation').hidden = true; $('#confirmation-message').textContent = '';
    $('#pedidos').scrollIntoView({ block: 'start' }); announce('Historial y avisos simulados borrados de esta pestaña.');
  });
  document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => setCategory(button.dataset.filter)));
  document.querySelectorAll('[data-category]').forEach(link => link.addEventListener('click', () => setCategory(link.dataset.category)));
  const menu = $('#navigation'); const menuToggle = $('#menu-toggle');
  function closeMenu(focus = false) {
    menu.classList.remove('open'); menuToggle.setAttribute('aria-expanded', 'false'); menuToggle.setAttribute('aria-label', 'Abrir menú'); menuToggle.textContent = '☰';
    if (focus) menuToggle.focus();
  }
  menuToggle.addEventListener('click', () => {
    const open = menuToggle.getAttribute('aria-expanded') !== 'true'; menu.classList.toggle('open', open);
    menuToggle.setAttribute('aria-expanded', String(open)); menuToggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú'); menuToggle.textContent = open ? '×' : '☰';
  });
  menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => closeMenu()));
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && menu.classList.contains('open')) closeMenu(true); });
  document.addEventListener('click', event => { if (!event.target.closest('.header')) closeMenu(); });
  window.matchMedia('(max-width: 800px)').addEventListener('change', () => closeMenu());
  $('#year').textContent = new Date().getFullYear();
  renderProducts(); renderCart(); renderOrders();
})();
