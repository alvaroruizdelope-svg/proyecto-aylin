# AYLIN SHOP · Django local, sin gastos de servicios

Tienda de demostración con seis productos, todos a **0,00 €**, y panel privado Django Admin. No se ha publicado ni activado dinero real. No hay contraseñas, cuentas bancarias operativas ni claves privadas incluidas.

Conserva diseño, fotografías, fichas, tallas/variantes, carrito y la sección general de opiniones antes del footer. Ahora los pedidos y opiniones se guardan realmente en SQLite mediante Django. Las opiniones permanecen pendientes hasta que un administrador autorizado las apruebe, sin inventar reseñas ni modificar estrellas.

## Windows: empezar

Instala Python gratuito y abre PowerShell en esta carpeta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Tienda: `http://127.0.0.1:8000/`. Panel: `http://127.0.0.1:8000/admin/`. Crea tus propias credenciales en el paso indicado; no hay una cuenta predeterminada. Para guardar opiniones usa Django, no Live Server. Si tu Python es otra versión compatible, ajusta el selector `py -3.12`.

## Incluido

- Panel con acceso real, hashes de Django, CSRF, permisos y bloqueo de intentos mediante django-axes.
- Resumen de SQLite, tabla/detalle de pedidos, moderación y auditoría.
- Perfil familiar separado a 1,00 € por producto, autenticado y con checkout monetario bloqueado.
- Ensayo administrativo opcional mediante fixtures claramente ficticios; nunca acredita dinero real ni envía correo.
- Cola persistente con Resend/SMTP preparados, desactivados sin configuración. No se ha probado correo real.
- Importación de solo lectura de datos del servidor anterior, copias y restauración.
- Bases y claves privadas fuera del repositorio, sin historial público ni PII de pedidos en el navegador.

Documentación:
- [Guía completa, Windows, panel y recuperación](GUIA.md)
- [Correo y requisitos pendientes](INTEGRACIONES.md)
- [Prueba familiar y transferencia bloqueada](TRANSFERENCIA.md)
- [Investigación de opciones gratuitas](SERVICIOS_GRATUITOS.md)
- [Borrador de conservación y eliminación](POLITICA_DATOS.md)
- [Fuentes/licencias de las fotografías](img/SHOP-FOTOGRAFIAS.md)

Pruebas Django: `.venv/bin/python manage.py test shop` (Windows: `.venv\Scripts\python.exe`). Prueba integral: `python tests/django_browser.py`, con Playwright y Chromium disponibles. Ver instrucciones en GUIA.md.

Probado en Linux y Chromium; Windows nativo y servicios externos quedan pendientes de comprobación. No se ha contratado hosting, dominio ni servicio de pago. La aplicación está limitada a acceso local y no debe exponerse mediante túneles/router como comercio.

## Descripción original conservada

# Proyecto Aylin

Página web de demostración para un estudio de manicura, pedicura y uñas acrílicas.

Desarrollada con HTML, CSS y JavaScript.
