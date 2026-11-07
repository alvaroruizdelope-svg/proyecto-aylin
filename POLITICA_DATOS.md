# Conservación y eliminación · Borrador para la prueba local

No es una política legal definitiva ni autorización para recoger datos de clientes comerciales. No se ha publicado la tienda. La finalidad actual es desarrollar y comprobar una demo local, usando datos ficticios. Antes de una prueba remota deben aprobarse responsable, destinatarios, plazos y condiciones concretas.

| Datos | Ubicación y acceso | Criterio preparado |
| --- | --- | --- |
| Carrito: IDs, tallas y cantidades | localStorage del navegador, sin datos de envío | El usuario puede vaciarlo; no contiene pedidos ni credenciales. |
| Confirmación actual | Memoria de la página, sin datos privados de envío | Desaparece al cerrar, recargar o cerrar la confirmación. |
| Pedidos demo y líneas | SQLite privado; administración con permiso | Sin borrado automático. Propuesta: revisar/borrar pruebas ficticias cuando se valide la entrega; antes conservar copia si se necesita depuración. |
| Prueba familiar pendiente/pagada | Base familiar separada y permisos específicos | Nunca aplicar la antigua limpieza de 24 horas. Revisar retención solo después de reconciliar cualquier prueba futura y acordar plazos contigo. No es una definición de obligaciones fiscales/comerciales. |
| Alias y opiniones | SQLite; solo las aprobadas son públicas | No extraer nombres del pedido. Conservar el contenido mientras se quiera publicar; retirar mediante moderación si incluye datos privados o su autor lo solicita y se verifica la petición. La eliminación definitiva y las copias deben coordinarse por el responsable. |
| Auditoría | SQLite privado, solo lectura en el panel | Conservar junto a los registros a los que da trazabilidad; no editar para ocultar acciones. Para datos reales se fijará un plazo aprobado. |
| Sesiones | Tabla Django, cookie HttpOnly/SameSite | Expiran al cerrar el navegador o tras una hora; `manage.py clearsessions` elimina sesiones caducadas sin borrar pedidos/opiniones. |
| Intentos de acceso | Tablas privadas django-axes | Bloqueo de 15 minutos después de cinco fallos. No equivale a borrado automático de registros. Revisar/limpiar por el operador con las herramientas de axes, sin publicar sus datos. |
| Avisos de correo | Outbox SQLite; proveedor solo si se autoriza | No interpretar queued como enviado. Conservar estados de aceptación y revisión; el proveedor y los buzones tienen retención independiente. No se han enviado mensajes reales. |

## Copias

Crear una copia consistente antes de importar, migrar o restaurar y al terminar una sesión importante de pruebas. Para una futura prueba remota: propuesta de copia diaria y prueba de recuperación; determinar contigo cuántas copias guardar, su destino privado fuera del equipo y el plazo de rotación. No se ha contratado almacenamiento. No se ha subido ninguna copia a terceros.

Las copias contienen datos privados y hashes de contraseñas, aunque no contengan claves API. Nunca GitHub, directorios públicos ni ZIP de entrega. Se pueden proteger con los controles/cifrado del sistema disponibles, sin comprar herramientas. La copia en el mismo disco no protege frente a pérdida del dispositivo.

## Procedimiento antes de borrar datos reales

Identificar perfil, registro, finalidad y autorización del responsable; detener procesos si se actúa sobre el archivo; conservar únicamente la copia privada cuya conservación esté justificada; eliminar o anonimizar de forma coherente pedidos, eventos, avisos y referencias; aplicar también la rotación de copias. Comprobar después que no se rompe integridad ni se revela información en la tienda. La eliminación forense de discos/copias no se garantiza mediante borrar una fila SQLite.

No se incluye una tarea automática que destruya datos para aparentar cumplimiento. La entrega conserva los datos hasta que se acuerde y ejecute un procedimiento explícito. No usar datos personales reales en tests, fixtures, logs técnicos ni archivos del repositorio.
