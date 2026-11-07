"""E2E local de Django con bases temporales, usuarios ficticios y correo desactivado.
Ejecutar con Python que tenga Playwright. Django se ejecuta con .venv o DJANGO_PYTHON.
"""
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
PYTHON=os.environ.get('DJANGO_PYTHON',str(ROOT/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')))
PASSWORD='browser-fixture-never-real-password-47!'

def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def run(env,*args):
    result=subprocess.run([PYTHON,str(ROOT/'manage.py'),*args],cwd=ROOT,env=env,capture_output=True,text=True)
    if result.returncode:raise AssertionError(result.stderr[-3000:])
    return result.stdout

def server(env):
    p=port();url=f'http://127.0.0.1:{p}'
    err=tempfile.TemporaryFile(mode='w+t')
    process=subprocess.Popen([PYTHON,str(ROOT/'manage.py'),'runserver',f'127.0.0.1:{p}','--noreload'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=err)
    process.test_stderr=err
    for _ in range(100):
        try:
            with urllib.request.urlopen(url,timeout=1):return process,url
        except Exception:time.sleep(.1)
    process.terminate();raise AssertionError('Django no ha iniciado')

def login(page,url,admin=True):
    page.goto(url+('/admin/login/' if admin else '/accounts/login/'))
    page.locator('[name=username]').fill('admin-fixture' if admin else 'buyer-fixture')
    page.locator('[name=password]').fill(PASSWORD)
    page.locator('input[type=submit], button[type=submit]').click()

def add(page,id,size=None):
    page.locator(f'[data-product-id="{id}"] .product-photo').click()
    if size:page.locator('#product-size').select_option(size)
    page.locator('#variant-add').click()
    assert not page.locator('#product-dialog').evaluate('(e)=>e.open')

with tempfile.TemporaryDirectory(prefix='aylin-django-e2e-') as folder:
    env=dict(os.environ,SHOP_PRIVATE_DIR=folder,SHOP_MAIL_ENABLED='false',DJANGO_SETTINGS_MODULE='config.settings')
    run(env,'migrate','--noinput')
    code="from django.contrib.auth import get_user_model;U=get_user_model();U.objects.create_superuser('admin-fixture','admin@example.com',"+repr(PASSWORD)+");U.objects.create_user('buyer-fixture','buyer@example.com',"+repr(PASSWORD)+")"
    run(env,'shell','-c',code)
    demo,url=server(env);family=None
    try:
        with sync_playwright() as p:
            executable=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium' if os.name!='nt' else '')
            browser=p.chromium.launch(headless=True,**({'executable_path':executable} if executable else {}),args=['--no-sandbox'])
            buyer=browser.new_context(viewport={'width':1440,'height':1000});page=buyer.new_page();page.emulate_media(reduced_motion='reduce');errors=[];external=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            def local(route):
                if route.request.url.startswith(url):route.continue_()
                else:external.append(route.request.url);route.abort()
            page.route('**/*',local);page.goto(url)
            assert page.locator('.product-card').count()==6
            assert all('0,00' in price for price in page.locator('.product-price').all_text_contents())
            assert page.locator('#product-dialog #review-form').count()==0
            assert page.locator('main > section').last.get_attribute('id')=='opiniones'
            for category,n in [('deporte',3),('mascotas',3),('todos',6)]:
                page.locator(f'[data-filter="{category}"]').click();assert page.locator('.product-card:visible').count()==n
            page.locator('[data-product-id="leggings"] .product-name').click();page.locator('#variant-add').click();assert 'Selecciona' in page.locator('#variant-error').inner_text();page.locator('#product-close').click()
            add(page,'leggings','S');add(page,'leggings','M');assert page.locator('.cart-line').count()==2
            page.locator('[data-cart-id="leggings:M"] .remove-button').click()
            page.locator('[data-cart-id="leggings:S"] [data-change="1"]').click();assert page.locator('[data-cart-id="leggings:S"] output').inner_text()=='2'
            page.locator('[data-cart-id="leggings:S"] [data-change="-1"]').click()
            for id in ['top','camiseta','arnes']:add(page,id,'S')
            for id in ['correa','juguete']:add(page,id)
            page.reload();assert page.locator('.cart-line').count()==6
            page.locator('#checkout-start').click();assert page.locator('#checkout-summary .summary-line').count()==6
            assert 'Talla S' in page.locator('#checkout-summary').inner_text()
            page.locator('#submit-order').click();assert not page.locator('#confirmation').is_visible()
            page.locator('#fill-demo').click();page.locator('[name=demoConsent]').check();page.locator('#submit-order').click();page.wait_for_selector('#confirmation:visible')
            assert page.locator('#confirmation-items li').count()==6
            assert '0,00' in page.locator('#confirmation-message').inner_text()
            assert 'en cola' in page.locator('#confirmation-mail').inner_text()
            assert 'ejemplo@example.com' not in page.locator('#confirmation').inner_text()
            assert page.locator('#orders,#pedidos').count()==0
            db=sqlite3.connect(Path(folder)/'demo/shop.sqlite3')
            assert db.execute('SELECT count(*) FROM shop_order').fetchone()[0]==1
            assert db.execute('SELECT count(*) FROM shop_orderline').fetchone()[0]==6;db.close()
            page.locator('#leave-review').click();page.locator('[name=publicName]').fill('Alias browser')
            page.locator('[name=rating][value="1"]').check();comment='Crítica de prueba. <img src=x onerror=alert(1)> Sin datos privados.'
            page.locator('[name=comment]').fill(comment);page.locator('#review-form button[type=submit]').click();expect(page.locator('#review-status')).to_contain_text('guardada')
            page.locator('#review-close').click();assert page.locator('.published-review').count()==0
            staff=browser.new_context(viewport={'width':1440,'height':1000});admin=staff.new_page();admin_errors=[]
            admin.on('pageerror',lambda e:admin_errors.append(str(e)))
            admin.on('console',lambda m:admin_errors.append(m.text) if m.type=='error' else None)
            login(admin,url)
            try: expect(admin.locator('.shop-dashboard')).to_be_visible(timeout=5000)
            except Exception:
                raise AssertionError('No se ha completado el acceso real al panel.')
            admin.goto(url+'/admin/shop/review/')
            admin.locator('input[name=_selected_action]').first.check();admin.locator('select[name=action]').select_option('approve');admin.locator('button[name=index]').click()
            admin.locator('[name=reason]').fill('Crítica legítima de una estrella sin datos privados');admin.locator('[name=confirmed]').check();admin.get_by_role('button',name='Confirmar moderación',exact=True).click()
            page.locator('#refresh-reviews').click();page.wait_for_selector('.published-review')
            assert 'Alias browser' in page.locator('.published-review').inner_text()
            assert comment in page.locator('.published-review').inner_text();assert page.locator('.published-review img').count()==0
            assert page.locator('.published-review time').get_attribute('datetime')
            page.reload();expect(page.locator('.published-review')).to_contain_text('Alias browser')
            assert not page.locator('#confirmation').is_visible()
            for w in [320,390,768,1024,1440]:
                page.set_viewport_size({'width':w,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),w
                page.locator('[data-product-id="arnes"] .product-photo').click();assert page.locator('#product-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth');page.locator('#product-close').click()
            page.set_viewport_size({'width':390,'height':844});page.locator('#opiniones').scroll_into_view_if_needed();page.screenshot(path='/tmp/aylin-django-shop-mobile.png')
            admin.goto(url+'/admin/shop/order/');admin.locator('#result_list .field-number a').first.click();assert 'Persona' not in admin.locator('h1').inner_text()
            admin.set_viewport_size({'width':390,'height':844});assert admin.evaluate('document.documentElement.scrollWidth<=innerWidth')
            admin.screenshot(path='/tmp/aylin-django-admin-mobile.png')
            assert not errors,errors;assert not admin_errors,admin_errors;assert not external,external
            # Perfil familiar distinto: autenticación, precios 1 EUR, compra bloqueada y fixture explícito.
            family_env=dict(env,DJANGO_SETTINGS_MODULE='config.settings_family');run(family_env,'migrate','--noinput');run(family_env,'shell','-c',code)
            run(family_env,'create_family_fixture','--username','buyer-fixture','--confirm-fictional')
            family,furl=server(family_env)
            fc=browser.new_context(viewport={'width':390,'height':844});fp=fc.new_page();fp.emulate_media(reduced_motion='reduce');fp.goto(furl);assert '/accounts/login/' in fp.url
            login(fp,furl,admin=False);assert all('1,00' in v for v in fp.locator('.product-price').all_text_contents())
            for id in ['leggings','top','camiseta','arnes']:add(fp,id,'S')
            for id in ['correa','juguete']:add(fp,id)
            assert '6,00' in fp.locator('#cart-total').inner_text();fp.locator('#checkout-start').click();assert fp.locator('#submit-order').is_disabled()
            assert 'bloqueado' in fp.locator('#checkout-mode').inner_text();assert '6,00' in fp.locator('#checkout-total').inner_text()
            fa=browser.new_context(viewport={'width':1440,'height':1000}).new_page();login(fa,furl)
            fa.goto(furl+'/admin/shop/order/');fa.locator('#result_list .field-number a').first.click();fa.get_by_role('link',name='Ensayar confirmación ficticia').click()
            fa.locator('[name=reason]').fill('Ensayo ficticio sin recibir ni transferir dinero');fa.locator('[name=confirmed]').check();fa.get_by_role('button',name='Confirmar operación',exact=True).click()
            fa.goto(furl+'/admin/');assert '6,00' in fa.locator('.shop-dashboard').inner_text();fa.screenshot(path='/tmp/aylin-django-dashboard.png')
            # El perfil familiar no ha cambiado el catálogo demo.
            page.reload();assert all('0,00' in v for v in page.locator('.product-price').all_text_contents())
            browser.close()
        # Copia/restauración real de una base Django temporal, sin datos personales reales.
        demo.terminate();demo.wait(timeout=10)
        backup=Path(folder)/'backups/demo-copy.sqlite3';run(env,'backup_database','--output',str(backup))
        run(env,'shell','-c',"from shop.models import Review;Review.objects.create(public_name='Alias temporal',rating=3,comment='Dato ficticio posterior a la copia')")
        run(env,'restore_database','--source',str(backup),'--confirm-server-stopped')
        db=sqlite3.connect(Path(folder)/'demo/shop.sqlite3');assert db.execute('SELECT count(*) FROM shop_review').fetchone()[0]==1;assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.close()
        print('PASS E2E Django: seis productos a cero, fichas/tallas/variantes, carrito, pedido persistido, opiniones guardadas/moderadas y conservadas, admin/login real, cinco tamaños, perfil familiar autenticado a 1 EUR separado y bloqueado, confirmación ficticia auditada y copia/restauración de SQLite. Sin correos ni transferencias reales.')
    finally:
        for process in [demo,family]:
            if process and process.poll() is None:process.terminate();process.wait(timeout=10)
