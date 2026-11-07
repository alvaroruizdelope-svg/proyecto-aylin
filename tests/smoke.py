"""Prueba integral local. Requiere Playwright y Chromium; no envía correo externo."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from app import Application, DemoServer, Store
from moderate import decide

with tempfile.TemporaryDirectory() as directory:
    app = Application(Store(directory))
    app.mailer.enabled = False  # Nunca usar credenciales reales durante pruebas automáticas.
    server = DemoServer(('127.0.0.1', 0), app)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'), headless=True, args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 1440, 'height': 1000})
            context.add_init_script("sessionStorage.setItem('aylin-shop-demo-orders-v1',JSON.stringify([{customer:{email:'old-private@example.com'}}]))")
            page = context.new_page(); errors, external = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
            def only_local(route):
                if route.request.url.startswith(url): route.continue_()
                else: external.append(route.request.url); route.abort()
            page.route('**/*', only_local)
            page.emulate_media(reduced_motion='reduce'); page.goto(url)
            assert page.locator('#orders, #pedidos, .order-record').count() == 0
            assert 'old-private@example.com' not in page.locator('body').inner_text()
            assert page.evaluate("sessionStorage.getItem('aylin-shop-demo-orders-v1')") is None
            assert page.locator('.product-card').count() == 6
            assert all('0,00' in x for x in page.locator('.product-price').all_text_contents())
            for category, count in [('deporte', 3), ('mascotas', 3), ('todos', 6)]:
                page.locator(f'[data-filter="{category}"]').click(); assert page.locator('.product-card:visible').count() == count
            def open_product(id, by_name=False):
                page.locator(f'[data-product-id="{id}"] .product-name' if by_name else f'[data-product-id="{id}"] .product-photo').click()
                assert page.locator('#product-dialog').evaluate('(e)=>e.open')
            def add_product(id, size=None, quantity=1):
                open_product(id)
                if size: page.locator('#product-size').select_option(size)
                page.locator('#product-quantity').fill(str(quantity)); page.locator('#variant-add').click()
                assert not page.locator('#product-dialog').evaluate('(e)=>e.open')
            open_product('leggings')
            page.locator('#variant-add').click()
            assert 'Selecciona una talla' in page.locator('#variant-error').inner_text()
            assert page.locator('.cart-line').count() == 0
            page.locator('#product-close').click()
            assert page.evaluate('document.activeElement.classList.contains("product-photo")')
            open_product('leggings', by_name=True); page.keyboard.press('Escape')
            add_product('leggings', 'S', 2); add_product('leggings', 'M')
            assert page.locator('.cart-line').count() == 2
            assert 'Talla: S' in page.locator('[data-cart-id="leggings:S"]').inner_text()
            page.locator('[data-cart-id="leggings:S"] [data-change="1"]').click()
            assert page.locator('[data-cart-id="leggings:S"] output').inner_text() == '3'
            page.locator('[data-cart-id="leggings:M"] .remove-button').click()
            assert page.locator('.cart-line').count() == 1
            page.reload(); assert page.locator('[data-cart-id="leggings:S"] output').inner_text() == '3'
            for id in ['top', 'camiseta', 'arnes']: add_product(id, 'S')
            for id in ['correa', 'juguete']: add_product(id)
            assert page.locator('.cart-line').count() == 6
            open_product('arnes'); assert 'fabricante' in page.locator('#size-guide').inner_text(); page.locator('#product-close').click()
            # Sin reseñas ficticias. Primer envío queda pendiente, no publicado.
            assert page.locator('#product-dialog #review-form, #product-dialog #published-reviews, .product-card .published-review').count() == 0
            assert page.locator('main > section').last.get_attribute('id') == 'opiniones'
            page.locator('#leave-review').click()
            page.locator('[name="publicName"]').fill('Alias de prueba')
            assert 'Aún no hay opiniones publicadas' in page.locator('#published-reviews').inner_text()
            page.locator('[name="rating"][value="2"]').check(); page.locator('[name="comment"]').fill('Una opinión de prueba anterior al pedido.')
            page.locator('#review-form button[type=submit]').click()
            expect(page.locator('#review-status')).to_contain_text('pendiente')
            assert page.locator('.published-review').count() == 0
            page.locator('#review-close').click()
            assert page.evaluate('document.activeElement.id') == 'leave-review'
            page.locator('#checkout-start').click()
            assert page.locator('#checkout-summary .summary-line').count() == 6
            assert 'Talla S' in page.locator('#checkout-summary').inner_text()
            assert 'Talla Única' in page.locator('#checkout-summary').inner_text()
            page.locator('#submit-order').click(); assert not page.locator('#confirmation').is_visible()
            page.locator('#fill-demo').click(); page.locator('[name="demoConsent"]').check()
            page.locator('#submit-order').click(); page.wait_for_selector('#confirmation:visible')
            assert page.locator('#confirmation-items li').count() == 6
            assert '0,00' in page.locator('#confirmation-message').inner_text()
            assert 'no enviado' in page.locator('#confirmation-mail').inner_text()
            confirmation = page.locator('#confirmation').inner_text()
            for private in ['Alex Demo', 'ejemplo@example.com', '600000000', 'Calle de Ejemplo']: assert private not in confirmation
            assert page.locator('.cart-line').count() == 0
            assert page.evaluate("!JSON.stringify(localStorage).includes('ejemplo@example.com')")
            assert page.evaluate("!JSON.stringify(sessionStorage).includes('ejemplo@example.com')")
            # Opinión negativa de compra demo: verificación solo servidor y aprobación manual, sin alterar puntuación.
            page.locator('#leave-review').click(); page.locator('[name="publicName"]').fill('Alias comprador'); page.locator('[name="rating"][value="1"]').check()
            comment = 'No me gusta. <img src=x onerror=alert(1)> Este texto es de prueba.'
            page.locator('[name="comment"]').fill(comment); page.locator('#review-form button[type=submit]').click()
            expect(page.locator('#review-status')).to_contain_text('pendiente')
            with app.store.connect() as db: row = db.execute('SELECT id,verified FROM reviews ORDER BY id DESC LIMIT 1').fetchone()
            assert row['verified'] == 1
            decide(app.store, row['id'], 'approved', 'Prueba de crítica negativa legítima, mostrada como texto')
            page.locator('#review-close').click(); page.locator('#refresh-reviews').click()
            page.wait_for_selector('.published-review')
            assert page.locator('.published-review .review-stars').get_attribute('aria-label') == '1 de 5 estrellas'
            assert 'Alias comprador' in page.locator('.published-review').inner_text()
            assert page.locator('.published-review time').get_attribute('datetime')
            assert 'ejemplo@example.com' not in page.locator('#opiniones').inner_text()
            assert comment in page.locator('.published-review').inner_text()
            assert page.locator('.published-review img').count() == 0
            assert 'verificada por el servidor' in page.locator('.published-review').inner_text()
            page.reload(); assert not page.locator('#confirmation').is_visible()
            assert page.locator('#orders, #pedidos').count() == 0
            other = browser.new_context(); other_page = other.new_page(); other_page.goto(url)
            assert not other_page.locator('#confirmation').is_visible()
            assert other_page.locator('#orders, #pedidos').count() == 0
            assert other.request.get(url + '/api/orders').status == 404
            assert other.request.get(url + '/api/admin/orders').status == 401
            for width in [320, 390, 768, 1024, 1440]:
                page.set_viewport_size({'width': width, 'height': 900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
                open_product('arnes')
                assert page.locator('#product-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth'), width
                page.locator('#product-close').click()
                page.locator('#leave-review').click()
                assert page.locator('#review-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth'), width
                page.locator('#review-close').click()
                assert page.locator('#opiniones').evaluate('(e)=>e.scrollWidth<=e.clientWidth'), width
            for img in page.locator('img').all():
                if img.get_attribute('id') != 'product-image':
                    img.evaluate('(e)=>e.loading="eager"'); img.evaluate('(e)=>e.decode()')
            assert page.locator('a[href^="#"]').evaluate_all('(els)=>els.every(a=>document.getElementById(a.getAttribute("href").slice(1)))')
            assert page.evaluate("async()=>{try{await AYLIN_PAYMENTS.createPaymentSession();return false}catch{return true}}")
            page.set_viewport_size({'width': 390, 'height': 844}); open_product('arnes'); page.screenshot(path='/tmp/aylin-detail-mobile.png'); page.locator('#product-close').click()
            assert not errors, errors
            assert not external, external
            # Vista estática sigue funcionando sin backend ni historial ni promesas de correo.
            class Quiet(SimpleHTTPRequestHandler):
                def log_message(self, *args): pass
            static = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
            threading.Thread(target=static.serve_forever, daemon=True).start()
            try:
                static_page = browser.new_page(); static_page.emulate_media(reduced_motion='reduce')
                static_page.goto(f'http://127.0.0.1:{static.server_port}')
                static_page.locator('[data-product-id="correa"] .product-photo').click()
                static_page.locator('#variant-add').click(); static_page.locator('#checkout-start').click()
                static_page.locator('#fill-demo').click(); static_page.locator('[name="demoConsent"]').check()
                static_page.locator('#submit-order').click(); static_page.wait_for_selector('#confirmation:visible')
                assert 'Prueba local sin registro' in static_page.locator('#confirmation-message').inner_text()
                assert 'no enviado en modo local' in static_page.locator('#confirmation-mail').inner_text()
                static_page.reload(); assert not static_page.locator('#confirmation').is_visible()
                static_page.locator('#leave-review').click()
                static_page.locator('[name="publicName"]').fill('Alias local')
                static_page.locator('[name="rating"][value="4"]').check()
                static_page.locator('[name="comment"]').fill('Opinión de prueba sin servidor para comprobar que no se guarda.')
                static_page.locator('#review-form button[type=submit]').click()
                expect(static_page.locator('#review-status')).to_contain_text('No se ha enviado ni guardado')
            finally: static.shutdown(); static.server_close()
            browser.close()
            print('PASS: fichas por foto/nombre; selección obligatoria de tallas; variantes independientes; seis productos a cero; cantidades; resumen con tallas; confirmación sin PII ni historial; aislamiento de sesiones; opiniones generales antes del footer sin reseñas en fichas, alias y fecha de publicación, moderación y verificación por servidor; texto seguro; modo estático; pagos intactos; cinco tamaños responsive y sin errores JS.')
    finally:
        server.shutdown(); server.server_close()
