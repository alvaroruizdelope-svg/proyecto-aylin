from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Sum, Q
from django import forms
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.conf import settings
import json
from .models import Order, OrderLine, OrderEvent, Review, ReviewEvent, Notification
from .services import transition_order, moderate

class ConfirmForm(forms.Form):
    reason = forms.CharField(label='Motivo / referencia de comprobación',min_length=5,max_length=500,widget=forms.Textarea(attrs={'rows':3}))
    confirmed = forms.BooleanField(label='Confirmo que he revisado la operación y sus datos')

class AylinAdminSite(admin.AdminSite):
    site_header = 'AYLIN SHOP · Administración privada'
    site_title = 'Aylin Shop · Panel'
    index_title = 'Gestión de la tienda de pruebas'
    index_template = 'admin/aylin_index.html'
    def index(self,request,extra_context=None):
        context=dict(extra_context or {})
        if request.user.has_perm('shop.view_order'):
            orders=Order.objects.filter(environment=settings.MODE)
            context['shop_summary']={'total':orders.count(),'pending':orders.filter(status=Order.Status.PENDING).count(),
                'paid':orders.filter(status=Order.Status.PAID).count(),'cancelled':orders.filter(status=Order.Status.CANCELLED).count(),
                'paid_minor':orders.filter(status=Order.Status.PAID).aggregate(value=Sum('total_minor'))['value'] or 0}
            cents=context['shop_summary']['paid_minor'];context['paid_eur']=f'{cents//100},{cents%100:02d} €'
        context['shop_mode']=settings.MODE
        return super().index(request,context)
site=AylinAdminSite(name='admin')

class ReadOnlyInline(admin.TabularInline):
    extra=0
    can_delete=False
    def has_add_permission(self,request,obj=None): return False
    def has_change_permission(self,request,obj=None): return False
class LineInline(ReadOnlyInline):
    model=OrderLine
    readonly_fields=['product_id','name','size','quantity','unit_price_minor']
class EventInline(ReadOnlyInline):
    model=OrderEvent
    readonly_fields=['created','actor','old_status','new_status','reason']

class OrderAdmin(admin.ModelAdmin):
    list_display=['number','created','buyer','products','total','method','status','environment','is_fixture']
    list_filter=['status','method','environment','is_fixture']
    search_fields=['number']  # Evitar PII en consultas URL/logs por búsquedas.
    inlines=[LineInline,EventInline]
    change_form_template='admin/shop/order/change_form.html'
    readonly_fields=[f.name for f in Order._meta.fields]+['buyer','total','shipping','bank_instructions']
    fieldsets=[('Pedido',{'fields':['number','created','environment','method','status','total','is_fixture','no_delivery']}),('Datos privados del comprador',{'fields':['buyer','shipping']}),('Instrucciones guardadas',{'fields':['bank_instructions']})]
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
    def get_queryset(self,request): return super().get_queryset(request).filter(environment=settings.MODE).prefetch_related('lines')
    @admin.display(description='Comprador')
    def buyer(self,obj): return obj.buyer_name
    @admin.display(description='Productos y tallas')
    def products(self,obj): return '; '.join(f'{i.name} · {i.size} × {i.quantity}' for i in obj.lines.all())
    @admin.display(description='Importe')
    def total(self,obj): return obj.total_eur
    @admin.display(description='Datos de envío de prueba')
    def shipping(self,obj): return format_html('<pre class="shop-private-text">{}</pre>',json.dumps(obj.customer,ensure_ascii=False,indent=2))
    @admin.display(description='Transferencia de este pedido')
    def bank_instructions(self,obj):
        return format_html('<pre class="shop-private-text">{}</pre>',json.dumps(obj.bank_snapshot,ensure_ascii=False,indent=2)) if obj.bank_snapshot else 'No se solicita transferencia para este pedido gratuito.'
    def get_urls(self):
        return [path('<uuid:object_id>/confirm-payment/',self.admin_site.admin_view(self.confirm_payment),name='shop_order_confirm_payment'),
                path('<uuid:object_id>/cancel/',self.admin_site.admin_view(self.cancel),name='shop_order_cancel')]+super().get_urls()
    def change_view(self,request,object_id,form_url='',extra_context=None):
        obj=self.get_object(request,object_id)
        context=dict(extra_context or {})
        context['can_confirm']=bool(obj and obj.method=='bank_transfer' and obj.status==Order.Status.PENDING and request.user.has_perm('shop.confirm_transfer'))
        context['money_released']=settings.FAMILY_MONEY_RELEASED or bool(obj and obj.is_fixture)
        context['can_cancel']=bool(obj and obj.status in [Order.Status.PENDING,Order.Status.DEMO] and request.user.has_perm('shop.cancel_order'))
        return super().change_view(request,object_id,form_url,context)
    def confirm_payment(self,request,object_id): return self.transition(request,object_id,Order.Status.PAID)
    def cancel(self,request,object_id): return self.transition(request,object_id,Order.Status.CANCELLED)
    def transition(self,request,object_id,target):
        obj=get_object_or_404(self.get_queryset(request),pk=object_id)
        perm='shop.confirm_transfer' if target==Order.Status.PAID else 'shop.cancel_order'
        if not self.has_view_permission(request,obj) or not request.user.has_perm(perm): raise PermissionDenied
        form=ConfirmForm(request.POST or None)
        if target==Order.Status.PAID:
            form.fields['confirmed'].label='Confirmo que es un ensayo ficticio, sin acreditar recepción real de dinero' if obj.is_fixture else 'He comprobado personalmente en mi banco que se ha recibido el importe'
        if request.method=='POST' and form.is_valid():
            try:
                changed=transition_order(request.user,obj.pk,target,form.cleaned_data['reason'])
                if changed: self.log_change(request,obj,f'Estado actualizado a {target}. Motivo: {form.cleaned_data["reason"]}')
                self.message_user(request,'Estado registrado con auditoría.' if changed else 'La operación ya estaba registrada; no se ha duplicado.',messages.SUCCESS)
                return redirect('admin:shop_order_change',object_id)
            except ValidationError as e: form.add_error(None,e.messages[0])
        context={**self.admin_site.each_context(request),'title':'Confirmar pago manualmente' if target==Order.Status.PAID else 'Cancelar pedido',
                 'object':obj,'form':form,'opts':self.model._meta,'is_fixture':obj.is_fixture}
        return TemplateResponse(request,'admin/shop/order/confirm.html',context)

class ReviewEventInline(ReadOnlyInline):
    model=ReviewEvent
    readonly_fields=['created','actor','decision','reason']
    fields=['created','actor','decision','reason']
class ReviewAdmin(admin.ModelAdmin):
    list_display=['id','public_name','rating','status','created','published_at','verified_demo']
    list_filter=['status','rating','verified_demo']
    readonly_fields=[f.name for f in Review._meta.fields]
    fields=['public_name','rating','comment','verified_demo','created','published_at','status','reason']
    inlines=[ReviewEventInline]
    actions=['approve','reject']
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
    def has_moderate_permission(self,request): return request.user.has_perm('shop.moderate_review')
    @admin.action(description='Aprobar opiniones seleccionadas (requiere confirmación)',permissions=['moderate'])
    def approve(self,request,queryset): return self.decide(request,queryset,'approved','approve')
    @admin.action(description='Rechazar opiniones seleccionadas (requiere motivo)',permissions=['moderate'])
    def reject(self,request,queryset): return self.decide(request,queryset,'rejected','reject')
    def decide(self,request,queryset,decision,action):
        if not self.has_moderate_permission(request): raise PermissionDenied
        form=ConfirmForm(request.POST if request.POST.get('apply') else None)
        if request.POST.get('apply') and form.is_valid():
            moderate(request.user,list(queryset.values_list('pk',flat=True)),decision,form.cleaned_data['reason'])
            for review in queryset: self.log_change(request,review,f'Moderación: {decision}. Motivo: {form.cleaned_data["reason"]}')
            self.message_user(request,'Moderación registrada sin alterar estrellas ni comentarios.',messages.SUCCESS)
            return None
        return TemplateResponse(request,'admin/shop/review/moderate.html',{**self.admin_site.each_context(request),
            'title':'Moderar opiniones','reviews':queryset,'form':form,'action':action,'decision':decision,'opts':self.model._meta})

class NotificationAdmin(admin.ModelAdmin):
    list_display=['id','order','event','status','attempts','created']
    list_filter=['status','event']
    readonly_fields=[f.name for f in Notification._meta.fields]
    fields=['order','event','status','attempts','created','first_attempt','next_attempt','provider_id']
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False

site.register(Order,OrderAdmin);site.register(Review,ReviewAdmin);site.register(Notification,NotificationAdmin)
site.register(User,UserAdmin);site.register(Group,GroupAdmin)
