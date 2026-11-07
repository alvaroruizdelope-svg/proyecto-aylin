# AYLIN SHOP · Servidor local, correo real y administración futura

## Estado y alcance

Servidor Python local de pruebas, SQLite fuera del checkout y sin dependencias externas. No desplegado ni apto para producción. Pagos PayPal, Apple Pay y transferencia **sin modificar y desactivados**. Todos los precios e importes siguen en cero.

Sí se implementó el cliente HTTPS oficial de Resend desde el servidor, con dos correos, lista de destinatarios de prueba, idempotencia y validación. No se ha enviado correo real: faltan credenciales/configuración. Las pruebas del proveedor usan dobles simulados y se identifican como tales.

## Qué debes configurar para enviar correos reales de prueba

1. Crea una cuenta en Resend. En **Domains**, añade un dominio o subdominio que controles, por ejemplo uno exclusivo de pruebas. Añade en tu proveedor DNS los registros exactos que solicite Resend y espera a que el dominio esté verificado. Consulta https://resend.com/docs/dashboard/domains/introduction . No se ha cambiado ningún DNS desde este proyecto.
2. Crea una clave API con permisos de envío y el alcance mínimo disponible para ese dominio. No la pegues en chat, archivos públicos ni GitHub.
3. Elige un remitente autorizado de ese dominio, un buzón vendedor de prueba y uno o varios buzones compradores que te pertenezcan o cuyos titulares hayan autorizado esta prueba. Los buzones pueden coincidir si el proveedor lo admite; revisa sus restricciones. Si usas un remitente de prueba proporcionado por Resend, respeta sus límites de destinatarios. El formulario debe usar un correo de la lista autorizada; deja ficticios nombre, teléfono y dirección.
4. Configura estas variables **privadas del proceso del servidor** mediante tu gestor seguro o terminal local. El navegador nunca las recibe. La aplicación no carga automáticamente un archivo `.env`.

| Variable | Uso |
| --- | --- |
| `RESEND_API_KEY` | Clave secreta de envío de Resend |
| `SHOP_MAIL_ENABLED` | `true` para solicitar envío; ausente/cualquier otro valor desactiva correo |
| `SHOP_MAIL_FROM` | Remitente autorizado; por ejemplo `Aylin Shop <pedidos@tu-dominio-verificado>` |
| `SHOP_SELLER_EMAIL` | Destinatario privado del vendedor |
| `SHOP_TEST_BUYER_EMAILS` | Lista de correos de compradores de prueba permitidos, separados por comas |
| `SHOP_PRIVATE_DIR` | Opcional: ruta privada de SQLite, fuera del proyecto y de toda raíz pública |

Ejemplo para Windows 11, en PowerShell, **reemplazando los marcadores** por tus datos. No copies una clave en un archivo:

```powershell
$secreto = Read-Host "Clave Resend (no se muestra)" -AsSecureString
$env:RESEND_API_KEY = [System.Net.NetworkCredential]::new('', $secreto).Password
$env:SHOP_MAIL_ENABLED = 'true'
$env:SHOP_MAIL_FROM = 'Aylin Shop <pedidos@TU-DOMINIO-VERIFICADO>'
$env:SHOP_SELLER_EMAIL = 'TU-BUZON-VENDEDOR'
$env:SHOP_TEST_BUYER_EMAILS = 'TU-BUZON-COMPRADOR'
$env:SHOP_PRIVATE_DIR = "$env:LOCALAPPDATA\AylinShop\private"
py server/app.py --port 8000
```

La clave queda en el entorno del proceso, no en JavaScript ni Git. Limita quién puede usar ese equipo; comprueba las ACL de la carpeta privada en Windows. Tras terminar, cierra el servidor y esa terminal o elimina las variables privadas de la sesión. No subas la carpeta privada. `.gitignore` excluye entornos y bases locales como defensa adicional; la aplicación rechaza un directorio privado dentro del checkout.

5. Abre **http://127.0.0.1:8000**, no Live Server. Añade los seis productos con sus tallas y cantidades, pulsa continuar y utiliza datos ficticios de envío con un correo comprador autorizado. Confirma el pedido demo gratuito.
6. El servidor llama a `https://api.resend.com/emails` con claves de idempotencia diferentes por destinatario. Solo marca **accepted** cuando obtiene respuesta de éxito con ID de proveedor. Comprueba ambos mensajes en el panel de Resend y luego en los buzones, incluido spam. La confirmación web distingue aceptación de entrega; no hay webhook de entregas implementado.
7. Para apagar los envíos, elimina `SHOP_MAIL_ENABLED` o establece un valor distinto de `true` y reinicia el servidor.

Si la configuración está incompleta, no se hace ninguna petición al proveedor. Si el comprador no está en la lista permitida, no se envía ninguno de los dos mensajes. Un error, timeout o respuesta sin ID queda como no confirmado, no como éxito. Un timeout puede significar que el proveedor recibió la solicitud; no se afirma que se haya enviado ni se reintenta automáticamente. La clave de idempotencia evita duplicar pedidos/correos al repetir la misma solicitud. Si un proceso se interrumpe después de registrar un pedido, el estado puede quedar pendiente; se necesita una cola durable y reconciliación antes de producción.

Los IDs de proveedor y contenido del pedido se conservan únicamente en SQLite privado. La API del checkout devuelve datos no personales y estados de correo; nunca direcciones ni claves. Los correos y el panel del proveedor tienen su propia retención y no se borran al limpiar SQLite.

Documentación oficial utilizada: https://resend.com/docs/api-reference/emails/send-email y https://resend.com/docs/dashboard/emails/idempotency-keys .

## Protección implementada y límites

- Solo loopback, comprobación de Host/Origin, cookie aleatoria HttpOnly/SameSite=Strict, token CSRF, consultas SQL parametrizadas, límites de cuerpo, sesión y frecuencia. CSP sin scripts de terceros ni `unsafe-eval`, no CORS abierto ni directorios estáticos listables.
- Validación de productos, tallas, disponibilidad demo, cantidades y datos en servidor; el catálogo servidor es la fuente de precios cero. Idempotencia por sesión y solicitud.
- Ningún GET de listados o detalles de pedidos. La respuesta del POST corresponde solo a la solicitud del comprador. No se conserva historial en el navegador y la confirmación actual desaparece al recargar.
- Base fuera del checkout, permisos de usuario en Unix, sin volcado de cuerpos/cookies/credenciales en logs. No es cifrado completo de disco: utiliza un equipo privado y cifrado del sistema si procede. Retención y limpieza descritas en GUIA.md.
- El HTTP local no usa cookies Secure; para una futura publicación serían imprescindibles HTTPS, cookies Secure, infraestructura y sesiones apropiadas. No basta con exponer este servidor mediante un proxy.

## Administración privada pendiente

No hay panel web, contraseña en cliente ni endpoints de pedidos que se protejan simplemente ocultándolos. `/admin` y `/api/admin/...` responden denegando acceso, sin entregar datos. La moderación CLI local usa los permisos del sistema operativo; no es una autenticación de administrador web.

Un panel real requiere proveedor de identidad o autenticación robusta, contraseñas con hash adecuado si las administra la aplicación, MFA recomendado, sesiones de servidor con expiración/revocación, protección CSRF, rol de administración y autorización comprobada **en cada endpoint**. También auditoría, paginación de pedidos, acceso mínimo a PII, copias protegidas, política de retención y borrado, gestión de incidencias y revisión de seguridad. No se ha implementado ni publicado ese panel para no aparentar una seguridad inexistente.

## Opiniones, verificación y moderación

API pública de lectura: opiniones generales aprobadas, con alias público elegido por su autor, estrellas, comentario y fecha de primera publicación. No devuelve nombre privado del comprador, correo, sesión ni pedido. El nombre público nunca se extrae de los datos de envío. El listado usa paginación de 20 reseñas con cursor. Envío con CSRF: las nuevas opiniones quedan pendientes, con alias/longitud/estrellas validadas y limitación de frecuencia. El servidor comprueba si esa sesión tiene un pedido demo registrado; no acepta marcas de verificación, correos ni números de pedido del cliente. La etiqueta pública dice específicamente **compra de demostración**. La API anterior por producto se conserva por compatibilidad, sin mostrar opiniones en fichas en la nueva web.

El operador local revisa mediante `server/moderate.py`. No rechazar críticas legítimas por baja puntuación: solo contenido abusivo, spam, datos personales o incumplimiento concreto. Las decisiones tienen motivo y fecha y no cambian la valoración ni el texto. Debe revisarse también que el alias y el comentario no expongan datos de contacto. La fecha de publicación solo se registra al aprobar por primera vez; no se inventa para opiniones antiguas que nunca la guardaron. La migración agrega columnas sin borrar reseñas ni modificar sus textos, estrellas o verificación. Opiniones y auditoría de moderación se conservan, sin el borrado de 24 horas aplicado a pedidos y sesiones de prueba. Antes de publicar una tienda real: cuentas o enlaces de un solo uso emitidos por servidor, acreditación de titularidad de pedido, reglas de moderación transparentes, denuncia/apelación, medidas antiautomatización y equipo de revisión. No se insertan opiniones de muestra.

## Pagos futuros (sin cambios en esta entrega)

PayPal necesita aplicación/cuenta Business y flujo oficial desde servidor. Apple Pay requiere proveedor compatible, dominio verificado, HTTPS y dispositivo/navegador elegibles. Transferencia requiere cuenta comercial y conciliación real, sin dar por pagado un pedido al pulsar un botón. En todos los casos: importes calculados en servidor y validación de webhooks firmados/idempotentes antes de marcar pagos. Esta demo no hace ninguna de esas operaciones ni pide datos bancarios.

## Transferencia: estructura interna incorporada, cobros todavía bloqueados

`server/bank_transfer.py` añade configuración privada `SHOP_BANK_TRANSFER_ENABLED`, `SHOP_BANK_BENEFICIARY` y `SHOP_BANK_IBAN`, validación IBAN y registros de prueba «Pendiente de pago». La configuración no activa el método comercial: el bloqueo de esta versión lo impide incluso si la variable se establece en `true`. No hay confirmación pública de pago ni administración ficticia. Los seis productos y el checkout siguen a cero.

Los detalles de diseño, persistencia, fixtures y requisitos de autorización/conciliación están en [TRANSFERENCIA.md](TRANSFERENCIA.md). No se ha modificado `js/integraciones.js` ni se han configurado cuentas reales.
