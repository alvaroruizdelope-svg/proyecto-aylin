import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

class Order(models.Model):
    class Status(models.TextChoices):
        DEMO = 'demo_confirmed', 'Demostración confirmada sin pago'
        PENDING = 'pending_payment', 'Pendiente de pago'
        PAID = 'paid', 'Pagado'
        CANCELLED = 'cancelled', 'Cancelado'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField('Número de pedido', max_length=100, unique=True)
    environment = models.CharField('Entorno', max_length=12, choices=[('demo','Demo gratuita'),('family','Prueba familiar')])
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    session_hash = models.CharField(max_length=64, blank=True)
    request_key = models.CharField(max_length=100)
    fingerprint = models.CharField(max_length=64)
    created = models.DateTimeField('Fecha', default=timezone.now)
    method = models.CharField('Método de pago', max_length=20, choices=[('free_demo','Demo gratuita'),('bank_transfer','Transferencia')])
    status = models.CharField('Estado', max_length=24, choices=Status.choices, default=Status.DEMO)
    total_minor = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default='EUR')
    customer = models.JSONField(default=dict)  # Solo DB privada, nunca respuesta/listado público.
    bank_snapshot = models.JSONField(default=dict)
    is_fixture = models.BooleanField('Ensayo ficticio sin dinero', default=False)
    no_delivery = models.BooleanField('Sin entrega de productos', default=True)
    receipt = models.JSONField(default=dict)
    legacy_key = models.CharField(max_length=160, unique=True, null=True, blank=True)
    class Meta:
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'
        constraints = [models.UniqueConstraint(fields=['session_hash','request_key','environment'], name='order_idempotency'),
            models.CheckConstraint(condition=models.Q(currency='EUR'),name='order_eur_only'),
            models.CheckConstraint(condition=(models.Q(environment='demo',total_minor=0,method='free_demo',status__in=['demo_confirmed','cancelled']) | models.Q(environment='family',total_minor__gt=0,method='bank_transfer',status__in=['pending_payment','paid','cancelled'])),name='order_environment_amount_state')]
        permissions = [('confirm_transfer','Puede confirmar transferencias recibidas'),('cancel_order','Puede cancelar pedidos')]
        ordering = ['-created']
    def __str__(self): return self.number
    @property
    def buyer_name(self): return self.customer.get('name', '')
    @property
    def total_eur(self): return f'{self.total_minor // 100},{self.total_minor % 100:02d} €'

class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='lines')
    product_id = models.CharField('Referencia', max_length=80)
    name = models.CharField('Producto', max_length=180)
    size = models.CharField('Talla', max_length=40)
    quantity = models.PositiveIntegerField('Cantidad')
    unit_price_minor = models.PositiveIntegerField('Precio unidad (céntimos)')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['order','product_id','size'], name='order_variant_unique'),models.CheckConstraint(condition=models.Q(quantity__gt=0),name='line_positive_quantity')]

class OrderEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    old_status = models.CharField('Estado anterior',max_length=24, blank=True, choices=Order.Status.choices)
    new_status = models.CharField('Estado nuevo',max_length=24,choices=Order.Status.choices)
    reason = models.TextField()
    created = models.DateTimeField('Fecha', default=timezone.now)
    class Meta: ordering = ['created','id']

class Review(models.Model):
    public_name = models.CharField('Alias público', max_length=60, blank=True)
    rating = models.PositiveSmallIntegerField('Estrellas')
    comment = models.TextField('Comentario')
    session_hash = models.CharField(max_length=64, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    verified_demo = models.BooleanField(default=False)
    created = models.DateTimeField('Fecha', default=timezone.now)
    published_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=[('pending','Pendiente'),('approved','Aprobada'),('rejected','Rechazada')], default='pending')
    reason = models.TextField(blank=True)
    legacy_product = models.CharField(max_length=80, blank=True)
    legacy_key = models.CharField(max_length=160, unique=True, null=True, blank=True)
    class Meta:
        verbose_name = 'opinión'
        verbose_name_plural = 'opiniones'
        constraints = [models.CheckConstraint(condition=models.Q(rating__gte=1,rating__lte=5), name='review_rating_range')]
        permissions = [('moderate_review','Puede moderar opiniones sin alterar valoraciones')]
        ordering = ['-id']
    def __str__(self): return f'Opinión {self.pk} · {self.rating}/5'

class ReviewEvent(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    decision = models.CharField(max_length=12)
    reason = models.TextField()
    created = models.DateTimeField('Fecha', default=timezone.now)
    legacy_key = models.CharField(max_length=160, unique=True, null=True, blank=True)

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications')
    event = models.CharField(max_length=24, choices=[('order_buyer','Pedido al comprador'),('order_seller','Pedido al vendedor'),('paid_buyer','Pago al comprador')])
    status = models.CharField('Estado del aviso',max_length=24, default='queued',choices=[('queued','En cola'),('sending','En curso'),('accepted','Aceptado por el servidor de correo'),('unconfirmed','Resultado no confirmado'),('needs_reconciliation','Requiere comprobación manual'),('not_configured','Correo no configurado'),('recipient_not_allowed','Destinatario no autorizado'),('fixture_no_mail','Fixture sin envío de correo')])
    payload = models.JSONField(default=dict)
    created = models.DateTimeField('Fecha', default=timezone.now)
    first_attempt = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    next_attempt = models.DateTimeField(default=timezone.now)
    provider_id = models.CharField(max_length=200, blank=True)
    class Meta:
        verbose_name = 'notificación de correo'
        verbose_name_plural = 'notificaciones de correo'
        constraints = [models.UniqueConstraint(fields=['order','event'], name='unique_order_notification')]

class RateLimit(models.Model):
    key = models.CharField(max_length=64, unique=True)
    count = models.PositiveIntegerField(default=0)
    starts = models.DateTimeField(default=timezone.now)

class LegacyArchive(models.Model):
    legacy_key = models.CharField(max_length=160, unique=True)
    kind = models.CharField(max_length=40)
    payload = models.JSONField()
    imported = models.DateTimeField(default=timezone.now)
