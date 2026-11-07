import json
from pathlib import Path
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, FileResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from .catalog import catalogue
from .models import Review
from .services import create_order, public_receipt, session_hash, submit_review, limit, CheckoutClosed


def locked_out(request, credentials=None, **kwargs):
    return render(request,'registration/locked.html',status=429)

def csrf_failure(request, reason=''):
    if request.path.startswith('/api/'):
        return JsonResponse({'error':'Sesión o token de seguridad no válido. Recarga la página.'},status=403)
    return HttpResponse('Solicitud de seguridad no válida. Recarga la página.',status=403)

def body_json(request):
    if request.content_type != 'application/json' or len(request.body)>24000: raise ValidationError('Solicitud JSON no válida o demasiado grande.')
    try: data=json.loads(request.body)
    except (ValueError,UnicodeDecodeError) as e: raise ValidationError('JSON no válido.') from e
    if not isinstance(data,dict): raise ValidationError('Solicitud no válida.')
    return data

@require_GET
def index(request):
    return HttpResponse((settings.BASE_DIR/'index.html').read_bytes(),content_type='text/html; charset=utf-8')

@require_GET
def session(request):
    if not limit('session-ip:'+request.META.get('REMOTE_ADDR',''),120,3600): return JsonResponse({'error':'Límite de sesiones de prueba alcanzado.'},status=429)
    session_hash(request)
    from .mail import configured
    return JsonResponse({'csrf':get_token(request),'mailConfigured':configured(),'mode':settings.MODE,
                         'checkoutEnabled':settings.MODE=='demo' or (settings.FAMILY_CHECKOUT_ENABLED and settings.FAMILY_MONEY_RELEASED)})

@require_GET
def runtime(request):
    return HttpResponse("'use strict';window.AYLIN_BACKEND=true;window.AYLIN_MODE="+json.dumps(settings.MODE)+';',content_type='text/javascript')

@require_GET
def catalog_js(request):
    text="'use strict';window.AYLIN_CATALOG="+json.dumps(catalogue(),ensure_ascii=False)+";AYLIN_CATALOG.products.forEach(p=>{p.variants.forEach(Object.freeze);Object.freeze(p.variants);Object.freeze(p)});Object.freeze(AYLIN_CATALOG.products);Object.freeze(AYLIN_CATALOG.categories);Object.freeze(AYLIN_CATALOG);"
    return HttpResponse(text,content_type='text/javascript; charset=utf-8')

@require_POST
def orders(request):
    if not limit('orders-ip:'+request.META.get('REMOTE_ADDR',''),60,3600): return JsonResponse({'error':'Límite de solicitudes alcanzado.'},status=429)
    try: order=create_order(request,body_json(request))
    except CheckoutClosed as e: return JsonResponse({'error':e.messages[0]},status=503)
    except ValidationError as e: return JsonResponse({'error':e.messages[0]},status=400)
    return JsonResponse(public_receipt(order),status=201)


def reviews(request):
    if request.method=='GET':
        raw=request.GET.get('cursor','')
        if raw and (not raw.isdigit() or len(raw)>18): return JsonResponse({'error':'Cursor no válido.'},status=400)
        rows=Review.objects.filter(status='approved')
        if raw: rows=rows.filter(id__lt=int(raw))
        rows=list(rows[:21]);more=len(rows)>20;rows=rows[:20]
        return JsonResponse({'reviews':[{'rating':r.rating,'comment':r.comment,'publicName':r.public_name or None,
                 'publishedAt':r.published_at.isoformat() if r.published_at else None,'verifiedDemo':r.verified_demo} for r in rows],
                 'nextCursor':rows[-1].id if more else None})
    if request.method!='POST': return JsonResponse({'error':'Método no permitido.'},status=405)
    if not limit('reviews-ip:'+request.META.get('REMOTE_ADDR',''),30,3600): return JsonResponse({'error':'Límite de solicitudes alcanzado.'},status=429)
    try: submit_review(request,body_json(request))
    except ValidationError as e: return JsonResponse({'error':e.messages[0]},status=400)
    return JsonResponse({'status':'pending','message':'Opinión guardada en la base de datos y pendiente de moderación. Todavía no está publicada.'},status=201)

@require_GET
def assets(request,folder,path):
    allowed={'css':{'.css'},'js':{'.js'},'img':{'.svg','.webp','.jpeg','.jpg','.png'}}
    root=settings.BASE_DIR/folder;file=(root/path).resolve()
    if folder not in allowed or root not in file.parents or file.suffix not in allowed[folder] or not file.is_file(): return HttpResponseNotFound()
    return FileResponse(file.open('rb'))

@require_GET
def admin_static(request,path):
    if '..' in Path(path).parts or not path.startswith(('admin/','shop/')): return HttpResponseNotFound()
    found=finders.find(path)
    if not found: return HttpResponseNotFound()
    return FileResponse(open(found,'rb'))

def denied_admin_api(request,path=''):
    return JsonResponse({'error':'No existe una API administrativa pública. Utiliza el panel autorizado.'},status=401 if not request.user.is_authenticated else 403)
