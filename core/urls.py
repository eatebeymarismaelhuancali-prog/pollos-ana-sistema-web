from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', views.dashboard, name='dashboard'),

    path('productos/', views.productos, name='productos'),
    path('productos/nuevo/', views.producto_editar, name='producto_nuevo'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('categorias/nueva/', views.categoria_nueva, name='categoria_nueva'),

    path('pos/', views.pos, name='pos'),
    path('pos/registrar/', views.registrar_venta, name='registrar_venta'),
    path(
    'analisis-geoespacial/',
    views.mapa_calor,
    name='mapa_calor'
),

    # MÓDULO DE CAJA
    path('caja/', views.caja, name='caja'),
    path('caja/abrir/', views.abrir_caja, name='abrir_caja'),
    path('caja/movimiento/', views.registrar_movimiento_caja, name='registrar_movimiento_caja'),
    path('caja/cerrar/', views.cerrar_caja, name='cerrar_caja'),

    path('cocina/', views.cocina, name='cocina'),
    path('cocina/<int:pk>/estado/', views.estado_pedido, name='estado_pedido'),

    path('ventas/', views.ventas, name='ventas'),
    path(
    'ventas/<int:pk>/comprobante/',
    views.comprobante_venta,
    name='comprobante_venta'
),
path(
    'ventas/<int:pk>/pdf/',
    views.descargar_nota_pdf,
    name='descargar_nota_pdf'
),
]