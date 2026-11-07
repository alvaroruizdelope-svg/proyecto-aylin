# Transferencia y perfil familiar · Preparación local, sin dinero real

## Perfiles y datos

La tienda demo normal conserva seis precios **0,00 €** y checkout gratuito. Django sirve el catálogo del perfil `config.settings_family` con **1,00 €** por unidad, sin cambiar el JSON ni el JavaScript estático base. Ese perfil exige login y usa otra base, clave y cookie. Una unidad de cada producto sumaría 6,00 €; las cantidades se calculan en servidor y no se acepta el total del navegador.

`FAMILY_CHECKOUT_ENABLED=False` y `FAMILY_MONEY_RELEASED=False` mantienen bloqueado el checkout familiar. No se habilitan mediante variables del entorno. No publiques esta versión ni realices transferencias. Cambiar los precios del perfil o introducir una cuenta no equivale a autorizar dinero real.

## Estructura implementada

Los modelos Django soportan estados demo_confirmed, pending_payment, paid y cancelled. El pedido registra líneas, tallas, cantidades, precios y total en céntimos; entorno; comprador privado; método y copia de las instrucciones bancarias del pedido. Una solicitud repetida de la misma sesión conserva su pedido y no duplica notificaciones. Reutilizarla con datos distintos se rechaza.

Las variables privadas futuras son `SHOP_BANK_BENEFICIARY` y `SHOP_BANK_IBAN`. No hay ningún dato bancario real configurado o incluido en GitHub. La validación de formato/checksum no acredita que una cuenta exista o pertenezca a su titular. Las instrucciones de cuenta solo se devolverían al comprador de ese pedido tras registro en servidor y si se autorizase expresamente la futura activación.

El banco no está integrado para leer saldos. No hay pagos automáticos. Las rutas públicas no pueden marcar pagado ni consultar pedidos ajenos. El panel comprueba autenticación, permiso de consulta y permiso especial `confirm_transfer`; requiere POST, CSRF, confirmación y motivo. La actualización y su auditoría son transaccionales y no se repiten al confirmar dos veces. Se prepara el aviso paid_buyer solo tras una transición válida.

La confirmación normal de transferencias monetarias sigue bloqueada con FAMILY_MONEY_RELEASED=False. Solo puede ensayarse sobre un pedido marcado explícitamente `is_fixture=True`, sin dinero, con cuenta sintética y notificaciones externas bloqueadas. Esto no acredita recepción real ni representa una venta. El panel identifica estos ensayos visiblemente.

## Ensayo local opcional del panel

Sigue primero los pasos de GUIA.md para migrar la base familiar y crear un administrador y usuario propios. Después puedes crear expresamente un fixture con `manage.py create_family_fixture --settings=config.settings_family --username TU-USUARIO --confirm-fictional`.

Este fixture añade los seis productos a 1,00 € a SQLite, con datos de envío y cuenta ficticios, sin enviar correo. No crea reseñas ni contraseñas. En el panel podrás abrir el pedido y usar **Ensayar confirmación ficticia**. La auditoría indicará tu usuario y fecha; el resumen refleja filas reales de la base, pero claramente como ensayos, no como dinero bancario recibido.

Los tests de Django habilitan los ajustes únicamente en memoria con una cuenta sintética, comprueban el registro pendiente de 6,00 € y la transición autorizada/auditada, y descartan la base temporal al finalizar. No modifican los ajustes normales ni ejecutan ninguna transferencia.

## Conservación

Los registros Django persisten al cerrar Chrome y el servidor; no se aplica la limpieza automática de 24 horas. Las bases y copias permanecen fuera de GitHub. Hay comandos de copia consistente y restauración comprobada. Es necesario decidir contigo retención y copias fuera del equipo antes de una prueba externa; no se usa una carpeta temporal como alojamiento comercial.

El módulo anterior `server/bank_transfer.py` se conserva como estructura legada y para sus pruebas; no es la entrada de Django ni una vía alternativa para habilitar pagos. Los fixtures antiguos pueden preservarse en un archivo lógico privado mediante `import_legacy`; no se convierten en pedidos comerciales.

## Qué falta para los 6,00 € reales

Aprobación separada del entorno externo y del dinero; plataforma gratuita comprobada sin tarjeta/cargos; HTTPS, cookies de producción y acceso restringido; ciclo fiable de tareas de correo; copias y recuperación; cuentas privadas; condiciones y retención de datos; nueva revisión de los bloqueos de la versión antes de autorizar la cuenta de Aylin/tu cuenta de prueba. No solicitamos tu IBAN en esta fase.

Con el entorno aprobado, el comprador tendría instrucciones de su pedido; tú comprobarías personalmente BBVA y confirmarías con tu cuenta administrativa. Un correo o una captura aportada por el comprador nunca deben considerarse por sí solos prueba de recepción bancaria.
