# AYLIN SHOP · Fichas, variantes, privacidad y opiniones

Seis productos y todos los importes a **0,00 €**. Diseño conservado. No hay pagos, ventas ni envíos reales. `js/integraciones.js` (PayPal, Apple Pay y transferencia) permanece sin cambios y desactivado.

## Dos maneras de usar la demo

### Vista estática (Live Server o abrir index.html)

Funciona el catálogo, las fichas, los filtros, tallas, cantidades, carrito y checkout gratuito. Solo se muestra la confirmación del pedido que se acaba de realizar, en memoria y sin datos de envío. No se guarda ni envía el pedido, no hay correos ni publicación de opiniones. La interfaz de opiniones indica que no ha enviado/guardado el comentario. La confirmación desaparece al recargar, cerrarla o comenzar otro checkout.

### Servidor de pruebas local (necesario para opiniones y correo)

Requiere Python 3.10 o superior. No requiere paquetes de ejecución externos. Desde la carpeta del proyecto:

```sh
python3 server/app.py --port 8000
```

En Windows normalmente puedes usar `py server/app.py --port 8000`. Abre `http://127.0.0.1:8000` en Chrome. El servidor solo escucha en loopback. No publicar, no enlazar un túnel y no usar como servidor de producción. No utiliza los archivos de la carpeta como raíz pública indiscriminada: solo permite HTML, CSS, JS e imágenes de rutas concretas.

`js/runtime.js` indica modo estático cuando se abre con Live Server. El servidor Python sustituye la respuesta de esa ruta en memoria para habilitar las operaciones de servidor; no modifica el archivo ni activa pagos.

## Fichas y tallas

Pulsa la foto o el nombre del producto. En la ficha tienes imagen grande, descripción, disponibilidad demo, talla, cantidad y botón de añadir. Escape, cerrar y volver al catálogo cierran la ficha y devuelven el foco al elemento de origen.

- Leggings, top y camiseta: XS, S, M y L; elección obligatoria, sin talla preseleccionada.
- Arnés: XS, S, M y L; guía provisional sin medidas inventadas. Confirmar cuello, pecho y peso con el fabricante.
- Correa y juguete: talla única.
- Leggings S y M son líneas independientes en carrito, resumen, confirmación y correo.
- Todas las variantes están inicialmente disponibles. `available: false` prepara el caso sin stock por talla. `demoLimit: 20` limita cantidades de prueba; no es inventario real ni se descuenta tras un pedido.

El catálogo canónico está en `data/catalogo.json`. Tras editarlo, ejecuta `python3 server/sync_catalog.py` para regenerar `js/catalogo.js`. El servidor valida los datos desde el JSON y nunca acepta nombres, precios o importes enviados por el navegador como autoridad.

## Privacidad de pedidos

Se ha eliminado la sección de historial, sus enlaces, avisos con datos de envío y toda persistencia de pedidos en el navegador. Al abrir esta versión se elimina la clave antigua `aylin-shop-demo-orders-v1` tanto de localStorage como de sessionStorage. No recupera ni muestra esos datos. Las copias de versiones anteriores que ya se hayan descargado no se pueden modificar remotamente: sustituye tu carpeta local por esta versión.

El carrito guarda exclusivamente identificadores de producto, tallas y cantidades bajo `aylin-shop-variants-v2`. No contiene correos, nombres, teléfonos ni direcciones.

En modo servidor, SQLite guarda los pedidos privados fuera del checkout público. En Linux, directorio 0700 y archivo 0600, rechazando enlaces simbólicos y rutas dentro del proyecto. Por defecto utiliza `/tmp/aylin-shop-private-<uid>`. En Windows utiliza `%LOCALAPPDATA%\AylinShop\private`: comprueba que sus ACL solo permitan el acceso de tu usuario y administradores del equipo. Puedes cambiarlo con `SHOP_PRIVATE_DIR`, siempre a una carpeta privada fuera del proyecto.

Al iniciar y al acceder al servidor se borran los registros de más de 24 horas (pedidos, sesiones, opiniones y auditoría). Si el servidor está detenido o inactivo los archivos pueden persistir hasta esa limpieza; tras las pruebas puedes borrar el directorio privado con el servidor parado. SQLite usa borrado de contenido de filas, pero esto no garantiza eliminación forense de copias, cachés o respaldos del sistema.

No hay API de historial, listados ni consulta de pedidos por número: GET `/api/orders` y `/api/orders/<id>` devuelven 404. El POST del pedido exige una cookie opaca HttpOnly/SameSite y CSRF; solo responde con la confirmación de esa solicitud, sus productos/tallas/cantidades y estados del correo, sin datos personales. El identificador o correo por sí solos no permiten consultar nada.

No existe panel administrativo web. `/admin` y `/api/admin/...` deniegan acceso. Falta autenticación, autorización de roles, sesiones seguras con HTTPS, auditoría y un panel conectado a endpoints protegidos; no hay contraseña en JS ni contenido privado ocultado mediante CSS.

## Opiniones

La ficha incluye valoración 1–5 y comentario de 10–2000 caracteres. No se incluyen nombres ni opiniones de ejemplo. En modo servidor se guardan por producto, siempre **pendientes de moderación**, con límites de frecuencia y sesión. Solo se muestran las aprobadas, con puntuación, comentario y marca de compra demo si corresponde; nunca datos del comprador o de su pedido.

La marca «Compra de demostración verificada por el servidor» depende de un pedido de ese producto registrado en el servidor y vinculado a la cookie HttpOnly de la sesión que escribe. La API rechaza campos como correo, número de pedido o `verified`. No equivale a una compra pagada ni a una identidad verificada. Para ventas reales se necesitará autenticación del comprador o invitaciones de un solo uso emitidas desde el servidor tras acreditar el pedido.

Moderación **manual local** por el operador que tiene acceso al equipo y al directorio privado (no es un panel web de administración):

```sh
python3 server/moderate.py --list
python3 server/moderate.py --id 1 --decision approved --reason "Comentario legítimo sin datos personales"
python3 server/moderate.py --id 2 --decision rejected --reason "Spam o insultos; motivo concreto de revisión"
```

Usa el mismo `SHOP_PRIVATE_DIR` del servidor si lo has configurado. Revisa cada texto antes de aprobar: spam, amenazas, insultos, enlaces abusivos o datos personales no deben publicarse. Las críticas negativas legítimas se aprueban sin alterar estrellas ni comentarios. Cada decisión registra motivo y fecha; la herramienta no edita el texto. No hay filtro automático que convierta valoraciones negativas en positivas. No introduzcas datos personales en comentarios. Las pruebas verifican que una valoración legítima de una estrella se puede publicar intacta.

## Correos reales de prueba

Consulta los pasos exactos en `INTEGRACIONES.md`. Actualmente no hay credenciales configuradas: no se ha enviado ningún correo real. Con el servidor y Resend configurados, se intentan enviar dos correos reales, exclusivamente a buzones de prueba autorizados. El estado distingue no configurado, destinatario no autorizado, solicitud aceptada por el proveedor y envío no confirmado. La aceptación no demuestra entrega al buzón.

Los correos incluyen identificador, productos, tallas, cantidades y total cero, e indican que no se enviará mercancía. El del vendedor añade los datos ficticios de envío y el estado demo. No hay claves ni dirección del vendedor en el código público. Los IDs de aceptación del proveedor se conservan en la base privada, no se exponen en la respuesta del checkout.

## Pruebas

```sh
python3 -m unittest discover -s tests -p test_server.py -v
python3 tests/smoke.py
```

El primer comando solo requiere Python. Comprueba validación de tallas/cantidades/datos, CSRF, Host/Origin, aislamiento de sesiones, ausencia de endpoints de pedidos, idempotencia, permisos de archivos, moderación y verificación de compra. Prueba el correo con un proveedor **simulado**; no sustituye una prueba real de Resend.

El segundo requiere Python + Playwright + Chromium (ruta opcional `CHROMIUM_PATH`), usa perfiles efímeros y bases privadas temporales. Prueba fichas por foto/nombre, talla obligatoria, S/M separadas, seis productos a cero, resumen y confirmación, borrado del historial antiguo, ausencia de PII en confirmación/almacenamiento, opiniones pendientes y moderadas, manejo de texto sin interpretar HTML, vista estática y tamaños 320/390/768/1024/1440. Desactiva expresamente el correo real en la prueba.

Ningún script de prueba publica la tienda ni realiza cobros. Falta probar entrega real de correos después de configurar el proveedor y buzones propios.
