import ipaddress
from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from urllib.parse import urlencode

class LocalOnlyMiddleware:
    """No hay variable para convertir esta entrega en un alojamiento de Internet."""
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        try: local = ipaddress.ip_address(request.META.get('REMOTE_ADDR','')).is_loopback
        except ValueError: local = False
        # testserver usa el cliente de pruebas, que normalmente tiene REMOTE_ADDR 127.0.0.1.
        if not local: return HttpResponseForbidden('Esta versión solo permite pruebas locales.')
        if settings.MODE == 'family' and not request.user.is_authenticated and not request.path.startswith(('/accounts/','/admin/','/static/','/css/','/img/')):
            if request.path.startswith('/api/'):
                from django.http import JsonResponse
                return JsonResponse({'error':'Acceso familiar autenticado requerido.'},status=401)
            return redirect(settings.LOGIN_URL + '?' + urlencode({'next':request.get_full_path()}))
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store'
        # Django Admin utiliza estilos inline propios. No se permiten scripts inline/eval.
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'"
        return response

def client_ip(request):
    return request.META.get('REMOTE_ADDR')
