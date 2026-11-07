# AYLIN SHOP · Integraciones futuras

## Estado actual: solo demo

No existe backend, base de datos, envío de correo ni pagos activos. Los seis precios son cero, el checkout solo crea un objeto de pedido local y los avisos se representan en pantalla. No hay claves privadas, SDK de pago ni credenciales de producción en el proyecto. Se verificaron los nombres de variables y configuración disponibles: no hay servicios ni credenciales de correo configurados. No se han enviado mensajes de prueba.

`js/integraciones.js` declara proveedores futuros con `enabled: false`, `mode: 'demo'` y un método `createPaymentSession` que siempre rechaza la operación. No basta con cambiar una bandera: es necesario implementar los servicios oficiales. El bloqueo permanece aunque se intente invocar el adaptador desde JavaScript.

## Contrato propuesto para un backend futuro (no implementado)

- `POST /api/orders`: recibe identificadores, variantes, cantidades, dirección y correo. El servidor valida campos, stock, impuestos, transporte y precios de su propia base de datos; ignora cualquier total enviado por el navegador. Responde con un pedido persistido y su estado real. Incluye idempotencia, control de abuso y protección CSRF si usa sesiones con cookies.
- `POST /api/orders/:id/payment-session`: el servidor autoriza el acceso al pedido, valida el método y crea una sesión oficial de pago. El cliente solo recibe el token/URL público necesario.
- Webhooks oficiales: validan firma, identidad del evento, moneda, importe y pedido; son idempotentes y registran estados como pendiente, autorizado, pagado o cancelado. Nunca marcar un pedido como pagado por un retorno del navegador.
- Cola de notificaciones: un evento persistido de pedido genera los correos del comprador y comercio; registrar reintentos, estados enviados/fallidos y evitar duplicados. El evento incluye número, productos y cantidades, total, datos de envío y estado. Los avisos actuales sirven como esquema visual, no como código de entrega de correo.
- Administración real: autenticación, permisos, control de acceso, auditoría, copias de seguridad y consulta protegida. El historial de esta demo carece de esas funciones deliberadamente y solo es local.
- Separar explícitamente pruebas y producción, secretos en servidor, HTTPS, política de privacidad, retención/borrado y monitorización sin exponer datos personales.

## PayPal

Cuenta PayPal Business, aplicación oficial y credenciales **sandbox** para desarrollo. Crear y capturar órdenes desde el servidor según el flujo oficial; validar eventos y cantidades antes de registrar pago. Solo el identificador público necesario puede estar en el cliente. Nunca un secreto en JavaScript o GitHub. Acordar en una fase posterior el paso autorizado a producción.

## Apple Pay

Proveedor compatible (por ejemplo Stripe), cuenta del comercio y claves de prueba; dominio verificado, HTTPS y habilitación oficial del método. La disponibilidad depende de región, cuenta, dispositivo y navegador compatibles. Validar la confirmación en el servidor/webhook del proveedor. Este borrador no muestra botones oficiales habilitados ni simula la aceptación de Apple Pay.

## Transferencia bancaria

Datos de la cuenta comercial confirmados, referencia única por pedido, instrucciones y proceso de conciliación. El pedido quedaría **pendiente de transferencia**, nunca pagado por pulsar un botón. Verificar recepción real antes de confirmar. La demo no muestra IBAN ni pide datos bancarios.

## Correos reales de prueba

Primero implementar el backend y elegir un servicio de pruebas, por ejemplo un buzón SMTP de sandbox o una cuenta de desarrollo de un proveedor transaccional. Harán falta host/puerto y credenciales SMTP, o una clave API del proveedor, dirección remitente autorizada, buzón del comercio y destinatarios de prueba permitidos. Para entrega externa pueden hacer falta dominio verificado, SPF/DKIM y configuración DMARC. Introducir credenciales solo por el gestor seguro del entorno/backend, nunca en chat, código cliente ni repositorio. No se requieren ni se solicitan valores para esta demo.

La comprobación posterior debe diferenciar solicitud aceptada por el servicio, entrega y recepción en el buzón. No declarar un correo enviado basándose en los avisos locales de esta tienda.
