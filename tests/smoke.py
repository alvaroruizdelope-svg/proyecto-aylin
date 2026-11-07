"""Prueba local de AYLIN SHOP. Requiere Python + Playwright + Chromium.
Ejecutar desde la raíz: python3 tests/smoke.py
No envía mensajes, no cobra y no consulta servicios externos.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{server.server_port}'

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'), headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors, external, failed = [], [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
        page.on('response', lambda r: failed.append(r.url) if r.status >= 400 else None)
        def local_only(route):
            if route.request.url.startswith(URL):
                route.continue_()
            else:
                external.append(route.request.url)
                route.abort()
        page.route('**/*', local_only)
        page.emulate_media(reduced_motion='reduce')
        page.goto(URL)
        assert page.title().startswith('AYLIN SHOP')
        assert page.locator('.product-card').count() == 6
        assert page.locator('.stock').all_text_contents() == ['En stock · demo'] * 6
        assert all('0,00' in x for x in page.locator('.product-price').all_text_contents())
        assert page.locator('#checkout-start').is_disabled()
        for category, count in [('deporte', 3), ('mascotas', 3), ('todos', 6)]:
            page.locator(f'[data-filter="{category}"]').click()
            assert page.locator('.product-card:visible').count() == count
        add = page.locator('[data-product-id="leggings"] button')
        add.click()
        page.locator('[data-cart-id="leggings"] [data-change="1"]').click()
        assert page.locator('[data-cart-id="leggings"] output').inner_text() == '2'
        page.locator('[data-cart-id="leggings"] [data-change="-1"]').click()
        assert page.locator('[data-cart-id="leggings"] output').inner_text() == '1'
        page.get_by_role('button', name='Eliminar Leggings deportivos del carrito', exact=True).click()
        assert page.locator('#checkout-start').is_disabled()
        for button in page.locator('.product-card button').all():
            button.click()
        assert page.locator('.cart-line').count() == 6
        assert page.locator('#cart-count').inner_text() == '6'
        page.reload()
        assert page.locator('.cart-line').count() == 6
        page.locator('#checkout-start').click()
        assert page.locator('#checkout').is_visible()
        assert page.locator('#checkout-summary .summary-line').count() == 6
        page.locator('#submit-order').click()
        assert page.locator('.order-record').count() == 0
        assert not page.locator('#checkout-form').evaluate('(f)=>f.checkValidity()')
        page.locator('#fill-demo').click()
        page.locator('[name="demoConsent"]').check()
        page.locator('[name="email"]').fill('incorrecto')
        assert not page.locator('#checkout-form').evaluate('(f)=>f.checkValidity()')
        page.locator('[name="email"]').fill('ejemplo@example.com')
        page.locator('[name="name"]').fill('   ')
        page.locator('#submit-order').click()
        assert 'Completa' in page.locator('#checkout-error').inner_text()
        page.locator('[name="name"]').fill('Alex Demo')
        page.locator('#submit-order').click()
        assert page.locator('#confirmation').is_visible()
        assert page.locator('.order-record').count() == 1
        assert page.locator('.cart-line').count() == 0
        assert page.locator('#checkout-start').is_disabled()
        first_id = page.locator('.order-content > .order-id').text_content()
        assert first_id.startswith('DEMO-')
        page.locator('.order-record > summary').click()
        assert page.locator('.order-content > ul > li').count() == 6
        assert page.locator('.sim-notification').count() == 2
        assert page.locator('.sim-notification ul li').count() == 12
        assert all('SIMULADO, NO ENVIADO' in text for text in page.locator('.sim-notification strong').all_text_contents())
        assert page.evaluate("!JSON.stringify(localStorage).includes('ejemplo@example.com')")
        page.reload()
        assert page.locator('.order-record').count() == 1
        assert page.locator('.cart-line').count() == 0
        # Nuevo pedido: identificador distinto y datos tratados como texto, sin HTML.
        page.locator('[data-product-id="correa"] button').click()
        page.locator('#checkout-start').click()
        page.locator('#fill-demo').click()
        page.locator('[name="name"]').fill('<img src=x onerror=alert(1)>')
        page.locator('[name="demoConsent"]').check()
        page.locator('#submit-order').click()
        assert page.locator('.order-record').count() == 2
        assert page.locator('.order-content > .order-id').first.text_content() != first_id
        assert page.locator('.order-content img').count() == 0
        page.locator('#clear-history').click()
        assert page.locator('.order-record').count() == 0
        assert page.evaluate("sessionStorage.getItem('aylin-shop-demo-orders-v1')") is None
        assert not page.locator('#confirmation').is_visible()
        # Manipulación del almacenamiento: descarta IDs y cantidades no válidas.
        page.evaluate("localStorage.setItem('aylin-shop-demo-cart-v1', JSON.stringify({leggings:999,top:-2,camiseta:1.5,inventado:3}))")
        page.reload()
        assert page.locator('.cart-line').count() == 1
        assert page.locator('[data-cart-id="leggings"] output').inner_text() == '20'
        assert page.locator('[data-cart-id="leggings"] [data-change="1"]').is_disabled()
        page.locator('[data-product-id="leggings"] button').click()
        assert page.locator('[data-cart-id="leggings"] output').inner_text() == '20'
        page.locator('#cart-clear').click()
        assert page.locator('#checkout-start').is_disabled()
        assert page.evaluate("async()=>{try{await AYLIN_PAYMENTS.createPaymentSession();return false}catch(e){return e.message.includes('desactivados')}}")
        for width in [320, 390, 768, 1024, 1440]:
            page.set_viewport_size({'width': width, 'height': 900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.locator('[data-product-id="leggings"] button').click()
            page.locator('#checkout-start').click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.locator('#cart-clear').click()
        page.set_viewport_size({'width': 390, 'height': 844})
        page.locator('#menu-toggle').click()
        page.locator('#navigation [data-category="mascotas"]').click()
        assert page.locator('#menu-toggle').get_attribute('aria-expanded') == 'false'
        assert page.locator('.product-card:visible').count() == 3
        for image in page.locator('img').all():
            image.evaluate('(e)=>e.loading="eager"')
            image.evaluate('(e)=>e.decode()')
            assert image.evaluate('(e)=>e.naturalWidth>0')
        # Todos los enlaces internos existen; las imágenes no dependen de terceros.
        assert page.locator('a[href^="#"]').evaluate_all('(links)=>links.every(a=>document.getElementById(a.getAttribute("href").slice(1)))')
        assert not external, external
        assert not failed, failed
        assert not errors, errors
        # Verifica la etiqueta sin stock mediante un catálogo controlado en otra página.
        stock_page = browser.new_page()
        catalog_text = (ROOT / 'js/catalogo.js').read_text().replace('"stockQuantity": 20', '"stockQuantity": 0', 1)
        stock_page.route('**/js/catalogo.js', lambda r: r.fulfill(body=catalog_text, content_type='text/javascript'))
        stock_page.goto(URL)
        assert stock_page.locator('.product-card').first.locator('button').is_disabled()
        assert stock_page.locator('.stock').first.inner_text() == 'Sin stock · demo'
        # La compra sigue disponible si el navegador bloquea almacenamiento.
        memory_page = browser.new_page()
        memory_page.add_init_script("Storage.prototype.getItem=function(){throw new Error('blocked')};Storage.prototype.setItem=function(){throw new Error('blocked')}")
        memory_page.goto(URL)
        memory_page.locator('.product-card button').first.click()
        memory_page.locator('#checkout-start').click()
        memory_page.locator('#fill-demo').click()
        memory_page.locator('[name="demoConsent"]').check()
        memory_page.locator('#submit-order').click()
        assert memory_page.locator('#confirmation').is_visible()
        assert memory_page.locator('#storage-warning').is_visible()
        print('PASS: catálogo de seis productos gratuitos, categorías, stock/sin stock, carrito y cantidades, persistencia, validación de checkout, pedido con seis productos, IDs distintos, historial y avisos simulados, borrado, almacenamiento manipulado/bloqueado, datos como texto, pagos bloqueados, menú, imágenes y cinco tamaños responsive. Cero errores JS/HTTP y cero peticiones externas.')
        browser.close()
finally:
    server.shutdown()
