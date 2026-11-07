# AYLIN SHOP · Demostración

Seis productos de ropa deportiva y mascotas, todos a **0,00 €**. Sin cobros ni envíos reales. No publicada en ningún alojamiento.

- Fichas de producto accesibles desde foto o nombre, con talla y cantidad.
- XS/S/M/L para ropa y arnés; talla única para correa y juguete; variantes independientes en carrito y resumen.
- Solo confirmación del pedido actual, sin historial público ni datos de envío en la confirmación. No se guardan pedidos en el navegador.
- Opiniones generales justo antes del footer, sin reseñas en fichas: alias público, estrellas, comentario y fecha de publicación; formulario independiente, moderación y verificación demo por sesión. Se conservan las opiniones antiguas sin inventar nombres ni fechas.
- Integración de correo real con Resend desde servidor, desactivada hasta configurar credenciales y buzones autorizados. **No se ha enviado ningún correo real en las pruebas.**
- Estructura de transferencia bancaria interna y desactivada: cuenta privada por entorno, cálculo en céntimos y registro pendiente solo para fixtures; ningún cobro comercial habilitado. [Detalles y límites](TRANSFERENCIA.md).
- No existe panel web administrativo inseguro: su autenticación y autorización real quedan documentadas como pendientes. Los pagos permanecen sin cambios y desactivados.

## Abrir

Modo estático: abre `index.html` con Live Server de VS Code (carrito y checkout locales; no guarda opiniones ni envía correo).

Modo de servidor de pruebas, Python 3.10+: `python3 server/app.py --port 8000` (Windows: `py server/app.py --port 8000`), luego abre `http://127.0.0.1:8000`. Solo escucha en loopback; no usar como alojamiento público.

- [Guía de uso, tallas, privacidad y moderación](GUIA.md)
- [Configurar correo, límites y administración futura](INTEGRACIONES.md)
- [Licencias de fotografías](img/SHOP-FOTOGRAFIAS.md)

Pruebas: `python3 -m unittest discover -s tests -p 'test_*.py' -v` y `python3 tests/smoke.py` (la segunda requiere Playwright y Chromium). Todas usan datos ficticios y correo simulado/desactivado, sin cobros.

Se conservan la descripción y recursos antiguos sin uso. No se incluyen bases de datos, pedidos ni credenciales en el repositorio.

## Descripción original conservada

# Proyecto Aylin

Página web de demostración para un estudio de manicura, pedicura y uñas acrílicas.

Desarrollada con HTML, CSS y JavaScript.
