'use strict';
// Contrato de extensión, no integración de pago. Ninguna clave ni SDK de producción.
// Activar un proveedor requiere implementar un backend: véase INTEGRACIONES.md.
window.AYLIN_PAYMENTS = Object.freeze({
  mode: 'demo',
  providers: Object.freeze([
    Object.freeze({ id: 'paypal', label: 'PayPal', enabled: false }),
    Object.freeze({ id: 'applepay', label: 'Apple Pay mediante proveedor compatible', enabled: false }),
    Object.freeze({ id: 'transfer', label: 'Transferencia bancaria', enabled: false })
  ]),
  async createPaymentSession() {
    throw new Error('Pagos desactivados. Se necesita una integración oficial y validación en el servidor.');
  }
});
