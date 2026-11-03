# Aylin Nails · Guía de la demo

Web estática sin instalaciones ni dependencias externas. La galería contiene 14 fotografías de Pexels almacenadas localmente y optimizadas en WebP; fuentes y licencia en `img/FOTOGRAFIAS.md`. Las ilustraciones SVG originales se conservan en portada y otras secciones. Ninguna imagen se presenta como trabajo de Aylin. No hay analítica, cookies publicitarias, backend ni reservas automáticas.

## Abrir la web

En VS Code abre la carpeta `proyecto-aylin`. Con la extensión Live Server instalada, haz clic derecho en `index.html` → **Open with Live Server**. Abre la dirección local que muestre la extensión en Chrome. También puedes abrir directamente `index.html` en Chrome; no hay módulos ni peticiones externas necesarias para mostrar el contenido.

## Cambiar contenido

- **WhatsApp:** modifica únicamente `WHATSAPP_NUMBER` al principio de `js/script.js`. Usa el formato internacional sin `+`, espacios ni guiones. Todos los enlaces se generan desde esa variable. Los mensajes se codifican con `encodeURIComponent`; abrir el enlace no envía nada ni confirma la reserva. Actualmente apunta al número de prueba autorizado.
- **Servicios y precios:** edita los objetos de `SERVICES` en `js/script.js`: `name`, `description` y `price`. El mensaje de WhatsApp toma automáticamente el nombre del servicio.
- **Galería:** edita `GALLERY` en ese mismo archivo. `image` es la ruta relativa desde `index.html`; `title` es el título, `alt` describe la imagen, y `price` es un número en euros de ejemplo, `author` y `source` conservan los créditos, `width` y `height` son las dimensiones del archivo, y `category` debe ser `acrilicas`, `manicura`, `disenos` o `pedicura`. Los filtros, contador y ampliación se actualizan automáticamente.
- **Fotografías:** guarda imágenes propias o autorizadas en `img/` (preferiblemente WebP/JPEG optimizados). Cambia las rutas en `GALLERY` y `NEWS`. Para portada y presentación, cambia `src`, `alt`, `width` y `height` de las imágenes correspondientes en `index.html`. Actualiza las etiquetas de demostración cuando proceda; no presentes imágenes ajenas como trabajos propios.
- **Novedades:** añade un objeto a `NEWS`: `title`, `date` en formato `AAAA-MM-DD`, `label`, `image`, `alt`, `description` y opcionalmente `content`. Solo se muestra «Leer más» si hay contenido adicional. Las fechas y publicaciones actuales están marcadas como ejemplos.
- **Colores y fuentes:** variables al principio de `css/estilos.css`. Se utilizan fuentes del sistema, sin descargas externas.
- **Textos, contacto y navegación:** `index.html`. Al confirmar Instagram, sustituye el texto pendiente por un enlace real y añádelo al pie. No hay enlaces sociales falsos.

## Datos que pedir a Aylin

Nombre y marca definitivos, presentación aprobada, fotografía y permiso de uso, servicios y descripciones reales, precios y condiciones, número comercial de WhatsApp, ubicación, horario, Instagram, fotografías propias y autorizaciones para publicar. Confirmar también la gestión manual de citas, cancelaciones y los datos del titular necesarios para preparar aviso legal y privacidad con asesoramiento adecuado.

Antes de publicar: sustituir las ilustraciones y textos provisionales, confirmar todos los datos y mensajes de contacto, preparar la información legal real, comprobar nuevamente móvil y escritorio y decidir cuándo retirar `noindex`. Esta entrega no publica ni configura ningún despliegue.

## Comprobaciones realizadas

Validación con Chromium automatizado sobre un servidor local temporal: seis servicios, tres novedades, once enlaces de WhatsApp con destino y mensajes correctos, cinco filtros, ampliación y navegación de imágenes, cierre por botón y Escape, retorno del foco, lectura ampliada de novedades, menú móvil y movimiento reducido. Todas las imágenes locales cargaron y no se registraron errores JavaScript. Sin desbordamiento horizontal a 320, 375, 390, 768, 1024 y 1440 píxeles. También se comprobaron rutas, anclas internas, IDs únicos y un único H1. No se enviaron mensajes ni se verificó la apertura de la aplicación externa de WhatsApp.

## Actualización de galería fotográfica

14 fotos locales con nombre de servicio y precio orientativo provisional en euros. Todos los precios se presentan como ejemplos, nunca tarifas oficiales. La ampliación muestra servicio, precio, aviso de demo, autor enlazado a Pexels y botón WhatsApp específico. Mantener estas aclaraciones y la documentación de licencias al sustituir fotografías.

Validación de esta actualización: 14 fotografías cargadas sin peticiones externas; cinco filtros (4 manicuras, 4 acrílicas, 3 diseños y 3 pedicuras); nombres, precios y destinos WhatsApp de las 14 ampliaciones; créditos enlazados; navegación con flechas, Escape y deslizamiento; foco devuelto al cerrar; menú móvil; anchos de 320, 390, 768, 1024 y 1440 píxeles sin desbordamiento. Sin errores JavaScript ni HTTP en Chromium. No se enviaron mensajes.
