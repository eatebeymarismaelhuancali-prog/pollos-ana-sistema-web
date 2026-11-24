from django.contrib import admin
from .models import Categoria,Producto,Venta,DetalleVenta,Pedido
admin.site.register(Categoria)
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
 list_display=('nombre','categoria','precio','activo')
 list_filter=('categoria','activo')
admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(Pedido)
