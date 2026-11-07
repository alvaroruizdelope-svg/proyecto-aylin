# Integraciones gratuitas · Django local

## Estado real

Presupuesto de contratación empleado: **0 €**. No se ha creado cuenta externa, contratado hosting, comprado dominio, activado pagos ni enviado correo real. Django, SQLite, django-axes y las herramientas de pruebas son gratuitas.

La aplicación actual funciona localmente con `manage.py`, no con `server/app.py`. El servidor antiguo se conserva para importar datos y comprobar compatibilidad. Las configuraciones privadas se leen del entorno y las bases/claves locales están fuera del proyecto; no se incluyen credenciales en GitHub.

## Cola de correo persistente

Al registrar un pedido, se crean en la misma transacción dos notificaciones: `order_buyer` y `order_seller`. Al confirmar una transferencia autorizada, se crea `paid_buyer`. Hay restricción única por pedido/evento, reclamación atómica del trabajo y estados explícitos: queued, sending, accepted, unconfirmed, needs_reconciliation, not_configured, recipient_not_allowed. Los fixtures no envían mensajes y usan fixture_no_mail.

- **queued** no significa enviado.
- **accepted** exige una respuesta de aceptación de la API o servidor SMTP; no prueba entrega al buzón.
- El proveedor Resend devuelve un ID de aceptación, conservado privadamente.
- En SMTP se guarda el Message-ID propio y solo se marca aceptado si el servidor no rechaza el destinatario. No se presenta ese Message-ID como ID de entrega del proveedor.
- Resend utiliza una clave de idempotencia estable. Los resultados inciertos solo se reintentan dentro de una ventana conservadora de 23 horas y pasan después a revisión manual.
- SMTP no garantiza idempotencia: una incertidumbre pasa a revisión sin reenvío automático para evitar duplicados.
- Antes de cualquier envío se exige la lista privada de correos de prueba permitidos. No se envía a un correo arbitrario introducido por un visitante.

Procesar avisos es un comando de servidor, nunca una llamada del comprador:

```powershell
.\.venv\Scripts\python.exe manage.py process_outbox
```

`--loop` comprueba periódicamente mientras esa terminal esté abierta. Para familia añade `--settings=config.settings_family`. Sin configuración completa no llama al proveedor. Deben configurarse las variables en la misma terminal antes de arrancar el worker; reiniciarlo al cambiar configuración. No se ejecuta automáticamente al instalar ni en las pruebas E2E.

## Resend Free: preparado, pendiente de aprobación/configuración

Variables privadas: `SHOP_MAIL_ENABLED=true`, `SHOP_MAIL_PROVIDER=resend`, `RESEND_API_KEY`, `SHOP_MAIL_FROM`, `SHOP_SELLER_EMAIL`, `SHOP_TEST_BUYER_EMAILS` (lista separada por comas).

Fuentes: https://resend.com/pricing y https://resend.com/docs/knowledge-base/403-error-resend-dev-domain . El plan gratuito anuncia 3.000 correos/mes y 100/día. No contratar un plan de pago ni añadir tarjeta para esta prueba. Si la plataforma exige pago o tarjeta, detener la configuración y revisarlo contigo.

**Sin dominio propio**, el remitente de prueba `resend.dev` solo puede enviar a la dirección del titular de la cuenta, según la documentación. Eso no demuestra que se puedan enviar correos a tu madre. Para otros destinatarios pide un dominio verificado. No vamos a comprar uno. Si no dispones de un dominio que ya controles, la alternativa siguiente puede ser más adecuada para una prueba mínima autorizada.

No se ha creado cuenta ni introducido una clave Resend en esta entrega. Si posteriormente autorizas la configuración, se debe comprobar aceptación en Resend y recepción en ambos buzones, incluido spam; no se ha implementado un webhook de entregas en esta fase local.

## Alternativa sin comprar dominio: SMTP de una cuenta Gmail propia

Se ha preparado un adaptador SMTP con TLS verificado (465/SSL o 587/STARTTLS), restringido a `smtp.gmail.com`. Sirve para una futura prueba familiar de bajo volumen, no para prometer entrega comercial masiva. No contrata Google Workspace ni añade una suscripción.

Requiere una cuenta propia que permita verificación en dos pasos y contraseñas de aplicación. Google puede no ofrecerlas por el tipo de cuenta o su política; consulta https://support.google.com/accounts/answer/185833?hl=es . Google recomienda métodos modernos como OAuth cuando son posibles; una integración OAuth completa no está incluida. No utilices tu contraseña principal ni una opción que desactive seguridad de la cuenta.

Solo cuando apruebes configurar y probar este servicio, podrías establecer en una terminal privada:

```powershell
$env:SHOP_MAIL_ENABLED = 'true'
$env:SHOP_MAIL_PROVIDER = 'smtp'
$env:SHOP_SMTP_HOST = 'smtp.gmail.com'
$env:SHOP_SMTP_PORT = '465'
$env:SHOP_SMTP_USER = 'TU-CUENTA-GMAIL'
$clave = Read-Host 'Contraseña de aplicación, nunca la principal' -AsSecureString
$env:SHOP_SMTP_PASSWORD = [System.Net.NetworkCredential]::new('', $clave).Password
$env:SHOP_MAIL_FROM = $env:SHOP_SMTP_USER
$env:SHOP_SELLER_EMAIL = 'TU-BUZON-DE-PRUEBAS'
$env:SHOP_TEST_BUYER_EMAILS = 'BUZONES-AUTORIZADOS-SEPARADOS-POR-COMAS'
.\.venv\Scripts\python.exe manage.py process_outbox
```

Son marcadores, no credenciales que puedas copiar sin configurar. El remitente debe corresponder a la cuenta SMTP. No copies la clave en archivos del proyecto ni en chat. La aplicación no carga `.env` automáticamente. Cierra esa terminal o elimina las variables después de la prueba. La aplicación y el proveedor tienen límites; no cambies a un plan de pago si se alcanzan.

No hay confirmación de correo real hasta que se realice esa configuración y comprobación con tu autorización. Las pruebas automáticas usan un proveedor simulado o correo expresamente desactivado, y no contactan Gmail ni Resend.

## Pagos

PayPal y Apple Pay continúan desactivados y sin cambios. La transferencia familiar usa estructura del servidor y un perfil separado a 1,00 € por unidad, pero el checkout monetario normal permanece bloqueado. No se solicita IBAN personal. Una variable bancaria no desbloquea el pago. Ver `TRANSFERENCIA.md`.

## Antes de Internet

No se incluye un despliegue público. El middleware rechaza clientes no locales, y solo se permiten hosts de loopback. Se utiliza HTTP de desarrollo local, con sesiones HttpOnly/SameSite y CSRF; HTTPS, cookies Secure, host autorizado y configuración de servidor externo requieren una fase revisada aparte, no basta retirar el middleware.

Antes de dinero real: comprobar la plataforma gratuita con tu cuenta y sus condiciones, HTTPS, persistencia, acceso restringido, ciclo de vida del worker, copias y restauración externa, retención, cuotas, protección de datos, permisos y autenticación administrativa (MFA recomendado para acceso remoto). No sustituir esas comprobaciones por ocultar URLs o poner `noindex`.
