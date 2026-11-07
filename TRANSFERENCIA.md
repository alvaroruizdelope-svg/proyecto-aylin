# Transferencia bancaria · Estructura desactivada

## Qué incluye esta versión

`server/bank_transfer.py` incorpora configuración privada, validación de cuenta, cálculo de importes desde un catálogo del servidor y un registro de pedidos de transferencia con estado **Pendiente de pago** (`pending_payment`). Es una estructura interna para preparar y probar la futura integración: **no es un método comercial activo**.

Los seis productos del catálogo real siguen a **0,00 €**. El HTML, CSS, fichas, tallas, carrito, opiniones, checkout gratuito y configuración pública de PayPal/Apple Pay/transferencia no cambian. El servidor añade una comprobación explícita para que el checkout gratuito rechace precios positivos o importes no enteros en lugar de confirmarlos a cero por error.

## Bloqueos que siguen vigentes

- La transferencia permanece desactivada por defecto.
- `BankTransferService.available_for_total(...)` devuelve falso en esta entrega, incluso con importe positivo y cuenta configurada. No se anuncia ningún método disponible para cobrar.
- `prepare_pending(...)` rechaza la operación comercial. Solo admite `test_only=True` desde código interno de pruebas; no hay ruta HTTP que acepte ese parámetro o permita invocar esa función.
- Todos los registros de esta estructura llevan `test_only=1`, `commercial=false`, prefijo `TEST-TRANSFER-` y aviso explícito de no transferir. La base rechaza registros comerciales y estados diferentes de pendiente.
- Ninguna ruta pública permite consultar las instrucciones, listar pedidos o marcar pagos. Las rutas administrativas existentes continúan denegando acceso.
- No se envían correos ni se realizan llamadas a un banco desde este módulo.

`test_only` no es un mecanismo de autenticación: es una herramienta interna de pruebas, no una opción de cliente, terminal de cobro o sustituto de la autorización pendiente.

## Configuración privada prevista

| Variable de entorno del servidor | Uso |
| --- | --- |
| `SHOP_BANK_TRANSFER_ENABLED` | Por defecto ausente/falso. `true` permite validar configuración en las pruebas internas, pero **no habilita pagos comerciales**. |
| `SHOP_BANK_BENEFICIARY` | Titular/beneficiario de la cuenta. Solo entorno privado, nunca HTML/JS. |
| `SHOP_BANK_IBAN` | IBAN privado. Se normalizan espacios y mayúsculas y se comprueban formato, longitud por país admitido y checksum módulo 97. |

No se han configurado valores reales. No debes facilitar tu IBAN personal para probar esta entrega. Los datos bancarios ficticios están únicamente en `tests/test_bank_transfer.py`, con BBAN compuesto por ceros: no corresponden a una cuenta operativa.

La validación de formato/checksum **no demuestra que la cuenta exista, pertenezca al beneficiario o permita recibir una transferencia**. La lista de países admitidos está explícita en el módulo y necesitará revisión para los países de venta definitivos. Los errores y la representación del objeto de configuración no incluyen cuenta ni beneficiario.

Para una futura cuenta de Aylin bastará sustituir las variables privadas para nuevos pedidos, después de implementar y autorizar la activación comercial. Cambiar las variables ahora no activa el checkout de transferencia. En el funcionamiento real futuro el comprador necesariamente verá el IBAN que debe utilizar, pero solo en las instrucciones de su pedido autorizado, no como configuración incrustada en el sitio o publicada en GitHub.

## Cálculo y registro de prueba

`quote_items` solo admite identificadores, tallas y cantidades, y toma precios/nombres del catálogo de servidor. Rechaza precios o totales enviados por el cliente, cantidades incorrectas y variantes no disponibles. Utiliza céntimos enteros, moneda EUR y un límite técnico de prueba; no usa coma flotante. Los precios positivos existen exclusivamente en copias de catálogo construidas por los tests, sin modificar `data/catalogo.json`.

El resultado de prueba de `prepare_pending` incluye:

- Identificador único de pedido y estado **Pendiente de pago**.
- Productos, tallas, cantidades, precios unitarios y subtotales del catálogo de servidor.
- Beneficiario e IBAN de prueba.
- Importe exacto en céntimos y texto decimal, moneda EUR.
- Concepto de transferencia igual al identificador único del pedido.
- Aviso de fixture ficticio, sin pago confirmado y sin realizar ninguna transferencia.

Se guarda de forma transaccional en la tabla privada `transfer_orders`, en la misma ubicación protegida fuera del checkout que el resto del servidor. El contenido privado conserva también los datos ficticios de envío. No usa localStorage, no crea un historial público ni introduce datos en archivos públicos.

La clave de idempotencia queda vinculada a la sesión. La repetición de una solicitud conserva el mismo identificador y las instrucciones originales, aunque después cambie la configuración bancaria o el precio del fixture. Cambiar cantidades o destinatario con la misma clave produce un error. Las variantes, moneda, importe y cuenta quedan congelados en el registro, no se recalculan silenciosamente después de confirmar.

Esta tabla está separada de los pedidos gratuitos de prueba: no se borra con la limpieza de 24 horas, no se utiliza para conceder la marca de comprador verificado y no modifica los datos existentes. Las pruebas usan directorios temporales y los eliminan al finalizar; no dejan pedidos ficticios en la base de la tienda ni en el ZIP.

## Qué falta para utilizar transferencias reales

1. Revisar y autorizar explícitamente una versión comercial. Eliminar los bloqueos de esta demo exige cambios de código y revisión; ninguna variable basta para activarla.
2. Implementar autenticación y autorización de administradores en servidor. Solo un administrador con permiso podrá confirmar recepción tras comprobar el banco. Registrar actor, fecha, importe, referencia y motivo; incluir controles contra repetición y concurrencia. No aceptar como prueba de pago una acción del comprador ni una captura de pantalla por sí sola.
3. Diseñar e implementar estados y transiciones comerciales: pendiente, pagado, cancelado, caducado y, cuando proceda, devolución. La tabla actual admite únicamente pendiente/test; se necesita una migración revisada, no actualizar su estado desde el navegador.
4. Exponer el futuro checkout positivo y sus instrucciones únicamente tras validar el pedido y su titularidad. Mantener los datos bancarios en servidor; no ofrecer una consulta pública por número de pedido. El modo estático seguirá sin poder crear pedidos comerciales.
5. Confirmar precios, impuestos, envío, descuentos, plazos de pago e inventario reales; calcular el total definitivo en servidor. El cálculo actual de fixtures es un subtotal de artículos, no un motor fiscal o logístico.
6. Usar almacenamiento duradero fuera de carpetas temporales, copias protegidas, recuperación, auditoría y una política de conservación adecuada para pedidos comerciales, separada de demos.
7. HTTPS, sesiones/cookies de producción, infraestructura, protección de datos y condiciones comerciales. Verificar la cuenta y beneficiario que autorice Aylin. El servidor actual solo escucha en loopback y no debe publicarse como comercio.
8. Adaptar las notificaciones y la consulta privada de pedidos al estado de transferencia: recibir un pedido pendiente o enviar un correo nunca debe marcarlo como pagado.

## Pruebas ejecutables

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/smoke.py
```

La batería del servidor incluye ocho pruebas nuevas de transferencia y las ocho existentes. Comprueba cuenta privada/desactivada, checksum, céntimos exactos, tallas, rechazo de importes del cliente, registro pendiente persistente, idempotencia, cuenta/importe congelados, aislamiento de sesión, no borrado por limpieza demo, bloqueo de estado pagado y ausencia de instrucciones/cobros en la API pública gratuita. Todos los importes positivos, beneficiarios y cuentas son fixtures ficticios; no hay conexiones a bancos ni correos reales.

La prueba de Chromium mantiene la comprobación del pedido con los seis productos gratuitos, tallas, carrito, confirmación privada, opiniones generales, moderación, modo estático y cinco tamaños de pantalla. No activa ninguna integración de pago.
