from django.urls import path
from django.contrib.auth import views as auth_views
from shop.admin import site
from shop import views
urlpatterns=[
 path('',views.index),path('index.html',views.index),path('favicon.ico',views.assets,{'folder':'img','path':'shop-icon.svg'}),
 path('api/session',views.session),path('api/orders',views.orders),path('api/reviews',views.reviews),
 path('api/admin/<path:path>',views.denied_admin_api),
 path('js/runtime.js',views.runtime),path('js/catalogo.js',views.catalog_js),
 path('accounts/login/',auth_views.LoginView.as_view(template_name='registration/login.html')),
 path('accounts/logout/',auth_views.LogoutView.as_view()),path('admin/',site.urls),
 path('static/<path:path>',views.admin_static),
 path('css/<path:path>',views.assets,{'folder':'css'}),path('js/<path:path>',views.assets,{'folder':'js'}),path('img/<path:path>',views.assets,{'folder':'img'}),
]
