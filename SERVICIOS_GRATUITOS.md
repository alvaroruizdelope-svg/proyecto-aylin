# Investigación de servicios gratuitos · 7 de noviembre de 2026

**No se ha contratado, registrado ni desplegado ningún servicio. Presupuesto de servicios y herramientas: 0 €.** Las consultas han sido de documentación pública; no hay comprobación con una cuenta real ni se ha pedido una tarjeta. Si un proveedor exige tarjeta, suscripción, upgrade o un coste, detener la configuración. No aceptar pruebas que pasen automáticamente a un plan de pago.

## Alojamiento

### PythonAnywhere Beginner: candidato, no aprobado como solución completa

Fuentes oficiales consultadas:
- https://www.pythonanywhere.com/pricing/
- https://help.pythonanywhere.com/pages/FreeAccountsFeatures/
- https://help.pythonanywhere.com/pages/AlwaysOnTasks/
- https://www.pythonanywhere.com/registration/register/beginner/

La documentación actual anuncia cuenta gratuita, SSL gratuito y 512 MiB de archivos privados. El formulario de registro gratuito consultado solo pide usuario, correo, contraseñas y aceptación de condiciones, sin campos de tarjeta. Las funciones actuales incluyen 100 segundos CPU para las tareas aplicables, una aplicación web con un worker, caducidad de un mes y dos consolas. Los planes gratuitos tienen acceso saliente restringido.

Las cuentas gratuitas nuevas **no incluyen las tareas diarias que tenían cuentas antiguas**. Las tareas always-on solo están disponibles en cuentas de pago. Por eso no se puede prometer que la cola persistente de correo se ejecute continuamente de forma gratuita ni que todos los destinos de correo estén permitidos. El límite de disco incluye bases, entorno y archivos; debe medirse antes de migrar las fotos/dependencias. La aplicación requiere renovación periódica; no es disponibilidad garantizada.

Puede ser un candidato para evaluar Django/SQLite con HTTPS y login propio en una futura fase autorizada. No he verificado persistencia, permisos, backup externo, envío ni restricciones de red con una cuenta. No hay un procedimiento de despliegue que retire los bloqueos actuales. No se declara cumplido el conjunto de requisitos de la prueba familiar de dinero.

### Render gratuito: descartado para SQLite persistente de esta prueba

Fuente: https://render.com/docs/free . El almacenamiento del servicio gratuito es efímero; no permite usar disco persistente como el plan de pago. La base PostgreSQL gratuita caduca a los 30 días y SMTP en puertos habituales está restringido en servicios gratuitos. No se contratará el plan de pago que se propuso anteriormente. No sustituiremos persistencia y seguridad por un montaje improvisado.

### Decisión de esta entrega

No se ha validado una opción totalmente gratuita que cumpla conjuntamente persistencia, HTTPS privado, tareas/notificaciones fiables y ausencia de tarjeta/cargos en una cuenta real. **Continuamos localmente**, tal como has indicado. Esto no afirma que no exista ninguna opción en el mercado; significa que no hay un entorno externo validado y autorizado en esta entrega. No publicaremos para aparentar que ya está listo.

## Correo sin dominio de pago

### Resend Free

Fuentes: https://resend.com/pricing y https://resend.com/docs/knowledge-base/403-error-resend-dev-domain . Plan gratuito publicado: 3.000 correos/mes y 100/día. El dominio de prueba solo permite enviar al propio correo de la cuenta; otros destinatarios requieren dominio verificado. No compraremos un dominio para esta fase. Si ya tienes uno autorizado se podría estudiar después, sin contratar nada adicional y comprobando las condiciones de alta.

### Cuenta Gmail propia para prueba familiar

Fuente: https://support.google.com/accounts/answer/185833?hl=es . Una cuenta elegible con verificación en dos pasos y contraseña de aplicación puede permitir SMTP TLS sin dominio comprado ni suscripción Workspace. La disponibilidad depende de la política de la cuenta; Google recomienda alternativas modernas cuando proceda. Se ha preparado el adaptador, pero no se han utilizado credenciales ni enviado correo. No uses la contraseña principal. No garantiza entrega y no es un compromiso de infraestructura comercial gratuita.

Consulta INTEGRACIONES.md antes de autorizar cualquier configuración. Primero deben verificarse cuota, restricciones, titularidad y destinatarios, sin añadir tarjeta o aceptar upgrades. Las pruebas de código usan solo proveedores simulados y bases temporales, no servicios reales.
