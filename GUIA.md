# AYLIN SHOP · Guía de la demostración

Tienda estática en HTML, CSS y JavaScript. Exactamente seis productos provisionales, todos a **0,00 €**: leggings deportivos, top deportivo, camiseta deportiva, correa para perro, arnés ajustable y juguete para mascotas. No hay ventas, pagos, correos ni envíos reales. Sin frameworks, dependencias de ejecución, rastreadores ni SDK de pagos.

## Abrir en tu ordenador

Descarga y extrae el ZIP de GitHub. Abre la carpeta extraída en VS Code, pulsa con el botón derecho en `index.html` y selecciona **Open with Live Server**. También puedes abrir `index.html` directamente en Chrome, aunque las reglas de almacenamiento con archivos locales dependen del navegador. Todos los recursos visuales cargan desde `img/`; no requieren acceso a Pexels. Los enlaces de atribución sí necesitan internet si decides abrirlos.

## Probar el flujo completo

1. Abre el catálogo y prueba los filtros Todos, Ropa deportiva y Mascotas.
2. Añade los seis productos. Cada precio, subtotal, envío demo y total es 0,00 €.
3. En Carrito cambia cantidades, elimina un producto y vuelve a añadirlo. El inventario demo permite hasta 20 unidades por producto; no representa existencias reales.
4. Pulsa **Continuar al pedido demo**. El resumen debe mostrar los seis productos.
5. Pulsa **Rellenar con datos ficticios de ejemplo**. Puedes editar estos datos, pero no introduzcas datos personales reales. Marca la confirmación de demostración.
6. Pulsa **Confirmar pedido demo**. Se genera un identificador `DEMO-…`, se vacía el carrito y aparece una confirmación sin cobro.
7. En **Pedidos de demostración** abre el detalle. Muestra productos, cantidades, total, datos ficticios y dos avisos etiquetados como SIMULADO, NO ENVIADO (comercio y comprador).
8. Recarga para comprobar el historial de la pestaña. Puedes borrarlo con su botón. No es un panel administrativo: solo muestra los pedidos de prueba de esa pestaña.

## Persistencia y límites

- Carrito: `localStorage`, clave `aylin-shop-demo-cart-v1`; solo identificadores de producto y cantidades. Se conserva al recargar. Se vacía con su botón.
- Historial y datos ficticios: `sessionStorage`, clave `aylin-shop-demo-orders-v1`; hasta 20 pedidos, últimos primero. Normalmente desaparece al cerrar la pestaña; la restauración de sesiones del navegador puede conservarlo. Utiliza **Borrar historial de esta pestaña** para eliminarlo explícitamente.
- Si el almacenamiento está bloqueado, hay una alternativa en memoria y se muestra un aviso. Los datos no se conservan al recargar en ese caso.
- No se transmiten formularios ni se realizan peticiones a APIs. Los avisos son representación local, no una bandeja de correo ni una cola real de notificaciones.
- Validación local adecuada para probar la demo; no protege un comercio real. Los datos de un navegador siempre pueden manipularse. No sirve como inventario, contabilidad ni registro comercial.

## Archivos y edición

- `index.html`: portada, secciones, formulario, contacto y apartados legales provisionales.
- `css/estilos.css`: variables de color y tipografía al principio. Paleta blanco cálido, grafito, oliva y arena.
- `js/catalogo.js`: seis productos y categorías. `priceMinor` está expresado en céntimos y debe permanecer en **0** en la demo. `stockQuantity` es inventario simulado (20 inicialmente); al establecerlo en 0 aparecen «Sin stock · demo» y el botón desactivado. El carrito elimina productos sin stock al recargar. No se reduce inventario tras los pedidos porque es una demo local sin gestión de existencias compartida.
- `js/script.js`: catálogo, filtros, carrito, validación, pedidos y avisos simulados. Los textos introducidos se muestran con `textContent`, nunca como HTML.
- `js/integraciones.js`: contrato de ampliación para pagos; proveedores desactivados. Solicitar una sesión de pago produce un error explicativo y no inicia ninguna comunicación.
- `img/shop-*.webp`, `img/shop-icon.svg`: imágenes activas de la tienda. Las seis fotos son referencias de Pexels, no fotografías de mercancía confirmada. Licencias y autores en `img/SHOP-FOTOGRAFIAS.md` y en la sección de créditos de la página.
- `INTEGRACIONES.md`: requisitos para pagos, backend y correo futuros.
- `tests/smoke.py`: prueba automatizada integral.
- Se conserva el README y los recursos anteriores sin uso para preservar el trabajo previo. La interfaz de tienda no carga imágenes, scripts ni estilos de manicura.

Para ampliar el catálogo: añade objetos en `products` de `js/catalogo.js`, con ID único y `priceMinor: 0`. Para categorías nuevas, añade su etiqueta al mapa `categories` y un botón con `data-filter` en HTML (y opcionalmente un enlace `data-category`). Sustituye las fotos por imágenes del producto real con permiso de uso, actualizando `image`, `alt`, `width`, `height`, `author` y `source`.

## Comprobación automatizada

En un entorno de desarrollo con Python, Playwright y Chromium instalados:

```sh
python3 tests/smoke.py
```

El navegador predeterminado es `/usr/bin/chromium`; puedes indicar otra ruta mediante `CHROMIUM_PATH`. Es una dependencia de pruebas, no de la tienda ni de Live Server. La prueba utiliza un servidor temporal de loopback y perfiles efímeros; no publica la tienda, no abre proveedores de pago y no envía correos.

Comprobado en Chromium: seis productos a cero, filtros, etiquetas stock/sin stock, cantidades y límite demo, eliminar/vaciar, persistencia del carrito, formulario inválido, compra de los seis productos, IDs distintos, historial y avisos simulados, borrado, almacenamiento alterado/bloqueado, tratamiento seguro de textos, adaptadores de pago bloqueados, menú móvil, imágenes y anchos 320/390/768/1024/1440 px. Sin errores JavaScript/HTTP ni solicitudes a servicios externos en el flujo probado. No se han probado integraciones reales porque no existen ni están activas.

## Datos que pedir a Aylin antes de una tienda real

Identidad fiscal y comercial, marca y contacto; especificaciones y fotografías de los seis productos reales; variantes, tallas, materiales y advertencias de uso; precios e impuestos definitivos; inventario, proveedores y facturación; países de venta, transportistas, plazos y portes; devoluciones, desistimiento y atención de incidencias; cuenta PayPal Business, proveedor de Apple Pay y cuenta bancaria comercial; proveedor de correo y dominio emisor. También hosting/backend, base de datos, responsable de privacidad, textos legales y consentimiento cuando corresponda. Todo requiere una nueva implementación y revisión antes de permitir compras públicas.
