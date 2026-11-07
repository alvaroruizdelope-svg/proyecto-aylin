'use strict';
(() => {
  const catalog = window.AYLIN_CATALOG;
  const products = catalog.products;
  const byId = new Map(products.map(p => [p.id, p]));
  const CART_KEY = 'aylin-shop-variants-v2';
  const $ = selector => document.querySelector(selector);
  const money = cents => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(cents / 100);
  const keyOf = (id, size) => `${id}:${size}`;
  const variantOf = (product, size) => product?.variants.find(v => v.size === size);
  let toastTimer, activeProduct, previousFocus, requestKey;
  let submitting = false;
  function node(tag, text, cls) {
    const e = document.createElement(tag);
    if (text !== undefined) e.textContent = text;
    if (cls) e.className = cls;
    return e;
  }
  function storageWarning() {
    $('#storage-warning').hidden = false;
    $('#storage-warning').textContent = 'El navegador no permite guardar el carrito. Se mantendrá solo mientras esta página esté abierta.';
  }
  // Elimina el historial de la versión anterior; nunca se lee ni se representa.
  for (const type of ['localStorage', 'sessionStorage']) {
    try {
      window[type].removeItem('aylin-shop-demo-orders-v1');
      window[type].removeItem('aylin-shop-demo-cart-v1');
    } catch { storageWarning(); }
  }
  function sanitize(raw) {
    const result = new Map();
    if (!Array.isArray(raw)) return [];
    for (const item of raw.slice(0, 100)) {
      if (!item || typeof item.id !== 'string' || typeof item.size !== 'string') continue;
      const product = byId.get(item.id); const variant = variantOf(product, item.size);
      if (!variant?.available || !Number.isInteger(item.quantity) || item.quantity <= 0) continue;
      const key = keyOf(item.id, item.size);
      const old = result.get(key)?.quantity || 0;
      result.set(key, { id: item.id, size: item.size, quantity: Math.min(old + item.quantity, variant.demoLimit) });
    }
    return [...result.values()];
  }
  let cart = [];
  try { cart = sanitize(JSON.parse(localStorage.getItem(CART_KEY) || '[]')); } catch { storageWarning(); }
  const apiReady = window.AYLIN_BACKEND ? fetch('/api/session', { credentials: 'same-origin', cache: 'no-store' })
    .then(async response => {
      if (!response.ok) throw new Error();
      const data = await response.json();
      if (typeof data.csrf !== 'string') throw new Error();
      $('#checkout-mode').textContent = data.mailConfigured
        ? 'Servidor de pruebas local: el pedido se registra de forma privada. Se intentarán enviar correos reales solo a destinatarios de prueba autorizados; utiliza uno de esos correos y datos ficticios de envío.'
        : 'Servidor de pruebas local: el pedido se registra de forma privada. El correo no está configurado y no se enviarán mensajes. Utiliza datos ficticios.';
      return data;
    }).catch(() => {
      $('#checkout-mode').textContent = 'No se puede conectar al servidor de pruebas. No confirmaremos un pedido sin su respuesta.';
      return null;
    }) : Promise.resolve(null);
  async function api(path, body) {
    const session = await apiReady;
    if (!session) throw new Error('No se puede acceder al servidor. Recarga para restablecer la sesión; no se ha mostrado una confirmación sin respuesta.');
    const response = await fetch(path, { method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': session.csrf }, body: JSON.stringify(body) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Operación no confirmada.');
    return result;
  }
  function announce(text) {
    clearTimeout(toastTimer); $('#toast').textContent = text;
    toastTimer = setTimeout(() => { $('#toast').textContent = ''; }, 4500);
  }
  function lines() { return cart.map(item => ({ ...item, product: byId.get(item.id) })); }
  function changedCart() {
    cart = sanitize(cart); requestKey = null;
    try { localStorage.setItem(CART_KEY, JSON.stringify(cart)); } catch { storageWarning(); }
    $('#checkout-error').textContent = ''; renderCart();
  }
  function setCategory(category) {
    const active = catalog.categories[category] ? category : 'todos';
    document.querySelectorAll('[data-filter]').forEach(b => { const on = b.dataset.filter === active; b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on)); });
    document.querySelectorAll('.product-card').forEach(card => { card.hidden = active !== 'todos' && card.dataset.category !== active; });
    $('#filter-status').textContent = `${products.filter(p => active === 'todos' || p.category === active).length} productos: ${catalog.categories[active] || 'Todos los productos'}`;
  }
  const dialog = $('#product-dialog');
  function openProduct(product, trigger) {
    activeProduct = product; previousFocus = trigger;
    $('#product-image').src = product.image; $('#product-image').alt = product.alt;
    $('#product-image').width = product.width; $('#product-image').height = product.height;
    $('#product-title').textContent = product.name; $('#product-description').textContent = product.description;
    $('#product-category').textContent = catalog.categories[product.category];
    $('#product-stock').textContent = product.variants.some(v => v.available) ? 'En stock · disponibilidad de demostración' : 'Sin stock · demostración';
    const sizes = $('#product-size'); sizes.replaceChildren();
    if (product.variants.length > 1) { const option = node('option', 'Selecciona una talla'); option.value = ''; sizes.append(option); }
    product.variants.forEach(v => { const option = node('option', `${v.size}${v.available ? '' : ' · Sin stock'}`); option.value = v.size; option.disabled = !v.available; sizes.append(option); });
    sizes.value = product.variants.length === 1 && product.variants[0].available ? product.variants[0].size : '';
    $('#product-quantity').value = 1; $('#product-quantity').max = 20;
    $('#variant-add').disabled = !product.variants.some(v => v.available);
    $('#size-guide').hidden = !product.sizeGuide; $('#size-guide').textContent = product.sizeGuide;
    $('#variant-error').textContent = '';
    dialog.showModal(); document.body.classList.add('modal-open'); dialog.scrollTop = 0;
  }
  let reviewCursor = null;
  let loadingReviews = false;
  let postingReview = false;
  async function loadReviews(reset = true) {
    if (loadingReviews) return;
    const container = $('#published-reviews');
    if (!window.AYLIN_BACKEND) { container.textContent = 'No hay opiniones publicadas disponibles en esta vista local. El envío y la consulta necesitan el servidor de pruebas.'; $('#more-reviews').hidden = true; return; }
    loadingReviews = true;
    $('#refresh-reviews').disabled = true; $('#more-reviews').disabled = true;
    if (reset) { reviewCursor = null; $('#more-reviews').hidden = true; container.textContent = 'Consultando opiniones…'; }
    try {
      await apiReady;
      const response = await fetch(`/api/reviews${!reset && reviewCursor ? `?cursor=${encodeURIComponent(reviewCursor)}` : ''}`, { cache: 'no-store' });
      if (!response.ok) throw new Error();
      const result = await response.json();
      if (reset) container.replaceChildren();
      if (!result.reviews.length && reset) container.append(node('p', 'Aún no hay opiniones publicadas. Puedes compartir tu experiencia con el botón «Dejar una opinión».', 'fine-print'));
      result.reviews.forEach(review => {
        const article = node('article', undefined, 'published-review');
        const heading = node('div', undefined, 'review-card-heading');
        heading.append(node('strong', review.publicName || 'Nombre público no facilitado'));
        if (review.publishedAt) {
          const date = new Date(review.publishedAt);
          const time = node('time', new Intl.DateTimeFormat('es-ES', { dateStyle: 'long', timeZone: 'Europe/Madrid' }).format(date));
          time.dateTime = review.publishedAt; heading.append(time);
        } else { heading.append(node('small', 'Fecha de publicación no registrada')); }
        const stars = node('div', `${'★'.repeat(review.rating)}${'☆'.repeat(5 - review.rating)}`, 'review-stars');
        stars.setAttribute('role', 'img'); stars.setAttribute('aria-label', `${review.rating} de 5 estrellas`);
        article.append(heading, stars, node('p', review.comment), node('small', review.verifiedDemo ? 'Compra de demostración verificada por el servidor' : 'Compra no verificada'));
        container.append(article);
      });
      reviewCursor = result.nextCursor;
      $('#more-reviews').hidden = !reviewCursor;
    } catch {
      if (reset) container.textContent = 'No se pueden consultar opiniones ahora. No se mostrarán valoraciones de ejemplo.';
      else announce('No se han podido cargar más opiniones. Puedes volver a intentarlo.');
    } finally { loadingReviews = false; $('#refresh-reviews').disabled = false; $('#more-reviews').disabled = false; }
  }
  const reviewDialog = $('#review-dialog');
  $('#leave-review').addEventListener('click', () => {
    $('#review-status').textContent = '';
    reviewDialog.showModal(); document.body.classList.add('modal-open');
  });
  $('#review-close').addEventListener('click', () => reviewDialog.close());
  $('#review-cancel').addEventListener('click', () => reviewDialog.close());
  reviewDialog.addEventListener('close', () => { document.body.classList.remove('modal-open'); $('#leave-review').focus(); });
  $('#refresh-reviews').addEventListener('click', () => loadReviews(true));
  $('#more-reviews').addEventListener('click', () => loadReviews(false));
  $('#product-size').addEventListener('change', () => {
    const variant = variantOf(activeProduct, $('#product-size').value);
    $('#product-quantity').max = variant?.demoLimit || 20; $('#variant-error').textContent = '';
  });
  $('#variant-form').addEventListener('submit', event => {
    event.preventDefault(); if (submitting) return;
    const size = $('#product-size').value; const variant = variantOf(activeProduct, size);
    if (!variant?.available) { $('#variant-error').textContent = 'Selecciona una talla disponible antes de añadir el producto.'; $('#product-size').focus(); return; }
    const quantity = Number($('#product-quantity').value);
    const existing = cart.find(item => item.id === activeProduct.id && item.size === size);
    if (!Number.isInteger(quantity) || quantity < 1 || quantity + (existing?.quantity || 0) > variant.demoLimit) {
      $('#variant-error').textContent = `El límite de demostración es de ${variant.demoLimit} unidades por talla, incluyendo las del carrito.`; return;
    }
    if (existing) existing.quantity += quantity; else cart.push({ id: activeProduct.id, size, quantity });
    changedCart(); dialog.close(); announce(`${activeProduct.name}, talla ${size}, añadido al carrito.`);
  });
  $('#review-form').addEventListener('submit', async event => {
    event.preventDefault(); const form = event.currentTarget;
    if (postingReview || !form.reportValidity()) return;
    if (!window.AYLIN_BACKEND) { $('#review-status').textContent = 'No se ha enviado ni guardado la opinión: esta vista no tiene servidor de opiniones.'; return; }
    const data = new FormData(form); const button = form.querySelector('button[type=submit]'); postingReview = true; button.disabled = true;
    try {
      const result = await api('/api/reviews', { publicName: String(data.get('publicName')).trim(), rating: Number(data.get('rating')), comment: String(data.get('comment')).trim() });
      $('#review-status').textContent = result.message; form.reset();
    } catch (error) { $('#review-status').textContent = error.message; }
    finally { postingReview = false; button.disabled = false; }
  });
  $('#product-close').addEventListener('click', () => dialog.close());
  $('#product-back').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { document.body.classList.remove('modal-open'); previousFocus?.focus(); });
  function renderProducts() {
    products.forEach(product => {
      const card = node('article', undefined, 'product-card'); card.dataset.category = product.category; card.dataset.productId = product.id;
      const photo = node('button', undefined, 'product-photo'); photo.type = 'button'; photo.setAttribute('aria-label', `Ver ficha de ${product.name}`);
      const image = node('img'); image.src = product.image; image.alt = product.alt; image.width = product.width; image.height = product.height; image.loading = 'lazy';
      const available = product.variants.some(v => v.available);
      photo.append(image, node('span', available ? 'En stock · demo' : 'Sin stock · demo', 'stock')); photo.addEventListener('click', () => openProduct(product, photo));
      const heading = node('div', undefined, 'product-title-row'); const h3 = node('h3'); const name = node('button', product.name, 'product-name'); name.type = 'button'; name.addEventListener('click', () => openProduct(product, name)); h3.append(name);
      heading.append(h3, node('span', money(product.priceMinor), 'product-price'));
      const options = node('button', 'Elegir opciones →', 'button'); options.type = 'button'; options.addEventListener('click', () => openProduct(product, options));
      card.append(photo, node('p', catalog.categories[product.category], 'product-tag'), heading, node('p', product.description, 'product-description'), options); $('#products').append(card);
      const li = node('li'); const credit = node('a', `${product.name} — ${product.author} / Pexels`); credit.href = product.source; credit.target = '_blank'; credit.rel = 'noopener noreferrer'; li.append(credit); $('#photo-credits').append(li);
    });
  }
  function quantityButton(item, change, text) {
    const button = node('button', text); button.type = 'button'; button.dataset.variant = keyOf(item.id, item.size); button.dataset.change = change;
    button.setAttribute('aria-label', `${change > 0 ? 'Aumentar' : 'Reducir'} ${item.product.name}, talla ${item.size}`);
    button.disabled = change > 0 && item.quantity >= variantOf(item.product, item.size).demoLimit;
    button.addEventListener('click', () => {
      if (submitting) return;
      const line = cart.find(i => i.id === item.id && i.size === item.size); if (!line) return;
      line.quantity += change; cart = cart.filter(i => i.quantity > 0); changedCart();
      const replacement = [...document.querySelectorAll('[data-variant]')].find(e => e.dataset.variant === keyOf(item.id, item.size) && Number(e.dataset.change) === change && !e.disabled);
      if (replacement) replacement.focus(); else $('#cart-total').focus();
      announce('Cantidad actualizada.');
    }); return button;
  }
  function renderCart() {
    const items = lines(); const count = items.reduce((n, item) => n + item.quantity, 0);
    $('#cart-count').textContent = count; $('#cart-count').setAttribute('aria-label', `${count} unidades en el carrito`);
    const target = $('#cart-items'); target.replaceChildren();
    if (!items.length) target.append(node('p', 'Tu próxima selección empieza aquí.', 'empty-cart'), node('p', 'Elige productos y tallas para probar el pedido gratuito.', 'empty-note'));
    for (const item of items) {
      const row = node('article', undefined, 'cart-line'); row.dataset.cartId = keyOf(item.id, item.size);
      const img = node('img'); img.src = item.product.image; img.alt = ''; img.width = 70; img.height = 85;
      const info = node('div'); info.append(node('h3', item.product.name), node('p', `Talla: ${item.size}`, 'variant-label'), node('span', '0,00 € / unidad', 'line-price'));
      const quantity = node('div', undefined, 'quantity'); quantity.append(quantityButton(item, -1, '−'), node('output', item.quantity), quantityButton(item, 1, '+')); info.append(quantity);
      const remove = node('button', 'Eliminar', 'remove-button'); remove.type = 'button'; remove.setAttribute('aria-label', `Eliminar ${item.product.name}, talla ${item.size}`);
      remove.addEventListener('click', () => { if (submitting) return; cart = cart.filter(i => keyOf(i.id, i.size) !== keyOf(item.id, item.size)); changedCart(); $('#cart-total').focus(); announce('Variante eliminada del carrito.'); });
      row.append(img, info, remove); target.append(row);
    }
    $('#cart-total').textContent = money(0); $('#cart-total').tabIndex = -1;
    $('#checkout-start').disabled = !items.length || submitting; $('#submit-order').disabled = !items.length || submitting;
    $('#cart-clear').hidden = !items.length;
    if (!items.length) $('#checkout').hidden = true;
    $('#checkout-summary').replaceChildren();
    items.forEach(item => { const row = node('div', undefined, 'summary-line'); row.append(node('span', `${item.product.name} · Talla ${item.size} × ${item.quantity}`), node('span', money(0))); $('#checkout-summary').append(row); });
    $('#checkout-summary').append(node('p', 'Envío de prueba: 0,00 €', 'fine-print'));
  }
  function closeConfirmation() {
    $('#confirmation').hidden = true; $('#confirmation-message').textContent = ''; $('#confirmation-items').replaceChildren(); $('#confirmation-mail').textContent = '';
  }
  $('#dismiss-confirmation').addEventListener('click', closeConfirmation);
  $('#checkout-start').addEventListener('click', () => {
    if (!cart.length || submitting) return;
    closeConfirmation(); $('#checkout').hidden = false; $('#checkout-title').focus(); $('#checkout').scrollIntoView({ block: 'start' });
  });
  $('#cart-clear').addEventListener('click', () => { if (submitting) return; cart = []; changedCart(); $('#cart-total').focus(); announce('Carrito vaciado.'); });
  $('#fill-demo').addEventListener('click', () => {
    if (submitting) return;
    const sample = { name: 'Alex Demo', email: 'ejemplo@example.com', phone: '600000000', address: 'Calle de Ejemplo, 1', postal: '28001', city: 'Ciudad de ejemplo', province: 'Provincia de ejemplo' };
    for (const [key, value] of Object.entries(sample)) $('#checkout-form').elements.namedItem(key).value = value;
    requestKey = null; announce('Datos ficticios rellenados. Para correos reales de prueba utiliza un buzón autorizado.');
  });
  $('#checkout-form').addEventListener('input', () => { if (!submitting) requestKey = null; });
  function mailStatus(status) {
    return ({ accepted: 'solicitud aceptada por el proveedor; entrega en buzón aún no confirmada', not_configured: 'no enviado: proveedor no configurado o desactivado', recipient_not_allowed: 'no enviado: destinatario de prueba no autorizado', pending: 'pendiente de confirmación del proveedor', unconfirmed: 'envío no confirmado por el proveedor; no se afirma que haya llegado', local: 'no enviado en modo local' })[status] || 'estado no confirmado';
  }
  $('#checkout-form').addEventListener('submit', async event => {
    event.preventDefault(); const form = event.currentTarget;
    if (submitting || !form.reportValidity()) return;
    const selected = lines(); if (!selected.length) return;
    if (window.AYLIN_PAYMENTS.mode !== 'demo' || selected.some(item => item.product.priceMinor !== 0 || !variantOf(item.product, item.size)?.available)) { $('#checkout-error').textContent = 'Solo se permiten variantes gratuitas y disponibles en esta demo.'; return; }
    const data = new FormData(form); const fields = ['name', 'email', 'phone', 'address', 'postal', 'city', 'province'];
    const customer = Object.fromEntries(fields.map(key => [key, String(data.get(key) || '').trim()]));
    if (Object.values(customer).some(v => !v) || customer.name.length < 3 || customer.address.length < 5 || customer.city.length < 2 || customer.province.length < 2) { $('#checkout-error').textContent = 'Completa los campos con datos de prueba válidos, sin dejar solo espacios.'; return; }
    if (data.get('demoConsent') !== 'on' || data.get('payment') !== 'demo') return;
    submitting = true; renderCart(); form.setAttribute('aria-busy', 'true'); $('#checkout-error').textContent = '';
    requestKey ||= globalThis.crypto?.randomUUID?.() || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-demo`;
    const items = selected.map(({ id, size, quantity }) => ({ id, size, quantity }));
    try {
      const receipt = window.AYLIN_BACKEND ? await api('/api/orders', { items, customer, demoConsent: true, requestKey }) : { id: `LOCAL-DEMO-${requestKey}`, items, totalMinor: 0, demo: true, mail: { buyer: { status: 'local' }, seller: { status: 'local' } } };
      if (!receipt.demo || receipt.totalMinor !== 0 || !Array.isArray(receipt.items) || typeof receipt.id !== 'string') throw new Error('Respuesta no válida. No se puede confirmar el pedido.');
      closeConfirmation();
      $('#confirmation-message').textContent = `Pedido ${receipt.id} · Total: 0,00 €. ${window.AYLIN_BACKEND ? 'Registro privado de demostración confirmado por el servidor.' : 'Prueba local sin registro en servidor.'}`;
      const list = node('ul');
      receipt.items.forEach(item => list.append(node('li', `${byId.get(item.id)?.name || 'Producto'} · Talla ${item.size} × ${item.quantity} · 0,00 €`)));
      $('#confirmation-items').append(list);
      $('#confirmation-mail').textContent = `Correo comprador: ${mailStatus(receipt.mail?.buyer?.status)}. Correo vendedor: ${mailStatus(receipt.mail?.seller?.status)}.`;
      cart = []; changedCart(); form.reset();
      $('#confirmation').hidden = false; $('#confirmation-title').focus(); $('#confirmation').scrollIntoView({ block: 'start' });
      announce('Pedido de demostración confirmado. No se ha realizado ningún cobro.');
    } catch (error) { $('#checkout-error').textContent = error.message || 'No se pudo confirmar el pedido. Puedes reintentar sin duplicarlo.'; }
    finally { submitting = false; form.removeAttribute('aria-busy'); renderCart(); }
  });
  document.querySelectorAll('[data-filter]').forEach(b => b.addEventListener('click', () => setCategory(b.dataset.filter)));
  document.querySelectorAll('[data-category]').forEach(a => a.addEventListener('click', () => setCategory(a.dataset.category)));
  const menu = $('#navigation'); const toggle = $('#menu-toggle');
  function closeMenu(focus = false) { menu.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-label', 'Abrir menú'); toggle.textContent = '☰'; if (focus) toggle.focus(); }
  toggle.addEventListener('click', () => { const open = toggle.getAttribute('aria-expanded') !== 'true'; menu.classList.toggle('open', open); toggle.setAttribute('aria-expanded', String(open)); toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú'); toggle.textContent = open ? '×' : '☰'; });
  menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => closeMenu()));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && menu.classList.contains('open')) closeMenu(true); });
  document.addEventListener('click', e => { if (!e.target.closest('.header')) closeMenu(); });
  window.matchMedia('(max-width: 800px)').addEventListener('change', () => closeMenu());
  $('#year').textContent = new Date().getFullYear();
  renderProducts(); renderCart(); loadReviews();
})();
