# AYLIN SHOP · Django local, presupuesto de servicios 0 €

Esta entrega ejecuta la tienda con Django y SQLite. No se ha contratado ni publicado nada, no se han enviado correos reales ni activado transferencias. El catálogo demo sigue a **0,00 €**. Los archivos del servidor anterior se conservan para importación y pruebas, pero la entrada de desarrollo actual es **manage.py**.

## 1. Instalar en Windows 11

Necesitas Python 3.12 o superior de https://www.python.org/downloads/windows/ (gratuito). La aplicación usa Django 5.2 LTS. Abre PowerShell en la carpeta extraída del ZIP, donde está `manage.py`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Si has instalado otra versión compatible, sustituye `py -3.12` por el selector de esa versión, o `py`. No necesitas activar scripts PowerShell, desactivar la política de ejecución, instalar Node ni introducir una tarjeta. Las dependencias son gratuitas. Elige tú el usuario y una contraseña robusta de al menos 12 caracteres en `createsuperuser`; no hay ninguna cuenta o contraseña predeterminada.

Abre **http://127.0.0.1:8000/** para la tienda y **http://127.0.0.1:8000/admin/** para el panel. Mantén abierta la terminal. Para parar, Ctrl+C; para arrancar de nuevo basta el último comando. Los datos permanecen en SQLite al parar o cerrar Chrome.

**Para enviar y guardar opiniones usa Django, no Live Server.** Abrir `index.html` o Live Server solo sirve como vista estática sin guardado de opiniones ni pedidos de servidor. No pulses el envío esperando un registro si estás en la vista estática: se indica que no se ha guardado.

En Linux/macOS: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt` y los mismos comandos de `manage.py` con `.venv/bin/python`.

## 2. Datos privados y conservación

Las bases y claves no se guardan en el proyecto ni se incluyen en GitHub/ZIP. Ubicación predeterminada:

- Windows: `%LOCALAPPDATA%\AylinShopDjango\demo\shop.sqlite3`.
- Linux/macOS: `$XDG_DATA_HOME/aylin-shop-django/demo/shop.sqlite3`, o `~/.local/share/aylin-shop-django/demo/shop.sqlite3` si no hay XDG_DATA_HOME.
- `SHOP_PRIVATE_DIR` permite elegir otra base privada, siempre fuera del repositorio. Dentro se separan `demo` y `family`, con bases y claves distintas.

Comprueba en Windows que las ACL del directorio solo permitan acceso a tu usuario y administradores del equipo. En Unix se crean carpetas 0700 y archivos 0600. Las claves aleatorias se generan por perfil en un archivo privado, sin secreto de desarrollo fijo en el código. No compartas esa carpeta, bases, copias o claves por GitHub.

No se aplica la antigua limpieza automática de 24 horas a los registros Django. Pedidos, opiniones y auditorías se conservan hasta que el responsable decida su eliminación. Esto evita perder una prueba pendiente. El borrador `POLITICA_DATOS.md` organiza finalidades, acceso y eliminación. Debes acordar antes de cualquier prueba externa cuánto conservar los datos, quién accede y cómo se eliminan también las copias. Usa datos ficticios de envío durante el desarrollo.

El navegador solo guarda productos, tallas y cantidades del carrito, no un historial de pedidos. La confirmación actual no contiene datos privados de envío y desaparece al recargar. No existe API pública de listados o detalles de pedidos.

## 3. Conservar datos del servidor anterior

No sobrescribas ni borres tu antigua base. Con el servidor detenido, conserva antes una copia privada. Después de `migrate`, importa explícitamente en el perfil demo, con una ruta real a tu archivo anterior:

```powershell
.\.venv\Scripts\python.exe manage.py import_legacy --source "RUTA-PRIVADA\shop.sqlite3"
```

El antiguo servidor usaba en Windows normalmente `%LOCALAPPDATA%\AylinShop\private\shop.sqlite3`. Comprueba que exista; si nunca lo ejecutaste o no tienes datos, no necesitas importar nada.

La importación abre el origen en **solo lectura**: no ejecuta su limpieza, no lo modifica ni borra. Conserva pedidos gratuitos y sus variantes, comentarios, estrellas, alias, fechas existentes y decisiones. Puede repetirse sin duplicar registros del mismo origen. Si no existía talla, alias, fecha o administrador, se indica que no está registrado; no se inventa. Los fixtures antiguos de transferencia se archivan privadamente y no se convierten en ventas. La importación se cancela íntegramente si detecta un error o colisión que deba revisarse. No hay datos de clientes incluidos por defecto en esta entrega.

## 4. Tienda, fichas y carrito

Se conserva el diseño, fotografías, catálogo y opiniones generales al final de la página antes del footer. Pulsa foto o nombre para abrir una ficha. Ropa y arnés requieren XS/S/M/L; correa y juguete tienen talla única. La guía del arnés no inventa medidas del fabricante.

S y M son líneas independientes en el carrito. Se pueden cambiar cantidades, eliminar y vaciar. El servidor valida IDs, tallas y cantidades y toma los precios de su catálogo; no acepta totales del cliente. El pedido demo de los seis productos vale cero. Doble clic/reintento con la misma solicitud conserva el pedido y no duplica sus notificaciones.

`data/catalogo.json` sigue siendo la base de seis productos gratuitos. Django sirve `/js/catalogo.js` a partir de esa base. Para mantener la vista estática al editar el catálogo, ejecuta `python server/sync_catalog.py`. La disponibilidad por variante es simulada, no un inventario comercial real.

## 5. Opiniones funcionales y moderación

Desde **Opiniones de nuestros clientes → Dejar una opinión**, escribe un alias público, estrellas y comentario. Al registrarse en SQLite aparece la confirmación; no aparece públicamente hasta aprobarlo. Puedes cerrar el navegador: el registro permanece. No se rellenan reseñas ni clientes de ejemplo.

En `/admin/`, entra en **Opiniones**, selecciona las pendientes y la acción Aprobar/Rechazar. Primero verás una pantalla de confirmación, con motivo obligatorio. Revisar también alias y datos privados. Una crítica negativa legítima se aprueba sin alterar texto ni estrellas. El panel no permite editar las valoraciones para mejorarlas. Se registra administrador, decisión, fecha y motivo. La fecha pública es la de primera aprobación; una fecha antigua desconocida no se inventa.

Solo se publican alias, estrellas, comentario, fecha y marca de verificación, nunca correo/dirección de un pedido. La verificación la calcula el servidor a partir de un pedido de la sesión/usuario: demo confirmado o prueba familiar pagada. No basta escribir un correo o identificador. No se concede por un pedido familiar pendiente. No equivale a una compra comercial.

## 6. Panel privado y permisos

Django Admin exige login. Contraseñas con hashes de Django, sesiones HttpOnly/SameSite, CSRF y bloqueo por cinco fallos de acceso durante 15 minutos mediante django-axes. Para desbloquear un ensayo fallido local, espera el plazo o utiliza `manage.py axes_reset` desde tu equipo privado. No se desactiva la protección para acceder.

El resumen usa SQLite: total de pedidos, pendientes, pagados, cancelados e importe marcado como pagado. Si no hay datos, muestra cero. La tabla muestra identificador, fecha, comprador, productos/tallas/cantidades, importe, método y estado. El detalle y los datos de envío solo son visibles con permiso. No se guardan PII en archivos públicos.

El superusuario administra todo. Para otros operadores, crea usuarios/grupos con los permisos mínimos desde el panel. Un operador de consulta necesita `view_order`; moderar exige `view_review` y `moderate_review`; confirmar transferencias exige `view_order` y `confirm_transfer`. Tener acceso de comprador o conocer la URL no concede esos permisos.

Las operaciones tienen pantalla de confirmación y auditoría. No se cambia el estado con un enlace GET. Una confirmación repetida de pago no duplica el evento ni el correo. No se comprueba el saldo de BBVA automáticamente. En esta versión solo se ensayan pagos con fixtures marcados como ficticios; los pedidos monetarios normales siguen bloqueados.

## 7. Perfil familiar separado a 1,00 €

No altera el catálogo demo y exige un usuario autenticado. Prepara su base y administrador aparte:

```powershell
.\.venv\Scripts\python.exe manage.py migrate --settings=config.settings_family
.\.venv\Scripts\python.exe manage.py createsuperuser --settings=config.settings_family
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001 --settings=config.settings_family
```

Accede al panel de ese puerto para crear, si quieres, un usuario normal de comprador (sin permisos staff). La tienda de `http://127.0.0.1:8001/` pedirá login. Cada producto muestra 1,00 €, los seis suman 6,00 € y el botón final está bloqueado. **No hagas ninguna transferencia.** No existe variable que libere dinero real: los ajustes `FAMILY_CHECKOUT_ENABLED` y `FAMILY_MONEY_RELEASED` permanecen falsos en la configuración normal.

Puedes practicar el panel con un único pedido completamente ficticio, solo si lo creas expresamente:

```powershell
.\.venv\Scripts\python.exe manage.py create_family_fixture --settings=config.settings_family --username TU-USUARIO-LOCAL --confirm-fictional
```

Este comando no crea opiniones ni contraseñas. Inserta un pedido claramente identificado como fixture, con cuenta sintética no operativa, sin entrega y sin correo. El panel permite **Ensayar confirmación ficticia**, registra quién hizo el ensayo y muestra sus cifras de la base como datos de prueba, nunca como dinero recibido. Los fixtures no envían correo aunque se configuren credenciales.

## 8. Copias y restauración

Elige un destino privado fuera del proyecto. La copia usa la API de SQLite, no una copia inconsistente del archivo en escritura:

```powershell
.\.venv\Scripts\python.exe manage.py backup_database --output "$env:LOCALAPPDATA\AylinShopBackups\demo-primera.sqlite3"
```

No sobrescribe copias existentes y comprueba integridad. Para restaurar, **detén servidor y worker**. La operación hace una copia previa y sustituye la base con una copia comprobada:

```powershell
.\.venv\Scripts\python.exe manage.py restore_database --source "$env:LOCALAPPDATA\AylinShopBackups\demo-primera.sqlite3" --confirm-server-stopped
```

Para el perfil familiar añade `--settings=config.settings_family`. Una copia en el mismo disco protege de algunos errores, no de perder el equipo. Para una prueba externa hará falta una copia fuera del dispositivo en un soporte privado disponible, con cifrado/controles de acceso y retención acordada. No hemos contratado almacenamiento ni enviado copias a terceros. Las bases no llevan cifrado propio: puedes usar la protección de tu sistema (por ejemplo BitLocker de tu Windows Pro). No subas copias al repositorio.

## 9. Correo y alojamiento

Consulta `INTEGRACIONES.md` y `SERVICIOS_GRATUITOS.md`. Hay cola persistente para pedido al comprador, aviso al vendedor y confirmación de pago. No se procesa en el navegador ni se declara enviado por estar en cola. No se ha configurado ni probado correo externo real. Se ha preparado Resend y una alternativa SMTP Gmail con TLS para una futura prueba familiar autorizada sin comprar dominio, cuando la cuenta lo permita.

El servidor está restringido a loopback. No es una configuración de Internet ni de producción. No publiques, no abras el router, no uses túneles, no lo conviertas en servicio público cambiando un único flag. HTTPS, acceso remoto, cuenta de hosting, credenciales reales y autorización de dinero siguen pendientes de revisión. No se ha contratado ningún servicio.

## 10. Pruebas de esta entrega

```powershell
.\.venv\Scripts\python.exe manage.py test shop
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Para la prueba de navegador opcional (dependencias gratuitas de desarrollo):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tests\django_browser.py
```

Pruebas ejecutadas en Linux con Python 3.12, Django, SQLite y Chromium: checkout y variantes, CSRF, precios separados, opiniones y moderación, permisos, login real y bloqueo, confirmaciones idempotentes, notificaciones con proveedor simulado, importación de solo lectura, persistencia, copia/restauración y vistas móviles/escritorio. Las pruebas E2E crean bases/usuarios/contraseñas ficticios solo en directorios temporales y desactivan el correo.

**No se ha podido ejecutar Windows nativo en este entorno Linux.** Se han preparado rutas Windows, comandos sin activación PowerShell, lectura UTF-8 y dependencia `tzdata`, pero el arranque en tu equipo debe comprobarse allí. Tampoco se han probado correos reales, HTTPS externo ni una transferencia bancaria. Los tests anteriores del servidor legado se conservan en `tests/test_server.py`, `tests/test_bank_transfer.py` y `tests/smoke.py`; no sustituyen las pruebas de Django.
