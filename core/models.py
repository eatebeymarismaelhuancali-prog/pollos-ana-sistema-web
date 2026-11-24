from django.db import models
from django.conf import settings
class Categoria(models.Model):
 nombre=models.CharField(max_length=80,unique=True)
 def __str__(self): return self.nombre
class Producto(models.Model):
 categoria=models.ForeignKey(Categoria,on_delete=models.PROTECT,related_name='productos')
 nombre=models.CharField(max_length=120)
 precio=models.DecimalField(max_digits=10,decimal_places=2)
 imagen=models.ImageField(upload_to='productos/',blank=True,null=True)
 activo=models.BooleanField(default=True)
 def __str__(self): return self.nombre
class Venta(models.Model):
 METODOS=[('efectivo','Efectivo'),('qr','QR'),('transferencia','Transferencia')]
 usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
 fecha=models.DateTimeField(auto_now_add=True)
 total=models.DecimalField(max_digits=12,decimal_places=2)
 metodo_pago=models.CharField(max_length=20,choices=METODOS)
 
 caja = models.ForeignKey(
     'Caja',
     on_delete=models.PROTECT,
     related_name='ventas',
     null=True,
     blank=True
 )

 def __str__(self): return f'Venta #{self.pk}'
class DetalleVenta(models.Model):
 venta=models.ForeignKey(Venta,on_delete=models.CASCADE,related_name='detalles')
 producto=models.ForeignKey(Producto,on_delete=models.PROTECT)
 cantidad=models.PositiveIntegerField()
 precio_unitario=models.DecimalField(max_digits=10,decimal_places=2)
 subtotal=models.DecimalField(max_digits=12,decimal_places=2)
class Pedido(models.Model):
 
 CANALES = [
    ('local', 'LOCAL'),
    ('delivery', 'DELIVERY'),
    ('llevar', 'LLEVAR'),
    ('pedidosya', 'PEDIDOSYA'),
    ('recoger_local', 'RECOGER_LOCAL'),
]

 ESTADOS=[('pendiente','Pendiente'),('preparacion','En preparación'),('listo','Listo'),('finalizado','Finalizado')]
 venta=models.OneToOneField(Venta,on_delete=models.PROTECT,related_name='pedido')
 canal=models.CharField(max_length=20,choices=CANALES)
 cliente=models.CharField(max_length=120,blank=True)
 observaciones=models.TextField(blank=True)
 estado=models.CharField(max_length=20,choices=ESTADOS,default='pendiente')
 creado=models.DateTimeField(auto_now_add=True)

class Caja(models.Model):
    ESTADOS = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
    ]

    usuario_apertura = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='cajas_abiertas'
    )

    fecha_apertura = models.DateTimeField(auto_now_add=True)

    monto_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default='abierta'
    )

    usuario_cierre = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='cajas_cerradas',
        null=True,
        blank=True
    )

    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True
    )

    monto_esperado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    monto_contado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    diferencia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    def __str__(self):
        return f'Caja #{self.pk} - {self.estado}'


class MovimientoCaja(models.Model):
    TIPOS = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ]

    caja = models.ForeignKey(
        Caja,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )

    tipo = models.CharField(
        max_length=10,
        choices=TIPOS
    )

    concepto = models.CharField(max_length=200)

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.tipo} - Bs {self.monto}'

class UbicacionDelivery(models.Model):
    pedido = models.OneToOneField(
        'Pedido',
        on_delete=models.CASCADE,
        related_name='ubicacion_delivery'
    )

    latitud = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    longitud = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    zona = models.CharField(
        max_length=120,
        blank=True
    )

    referencia = models.CharField(
        max_length=250,
        blank=True
    )

    enlace_ubicacion = models.TextField(
        blank=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Ubicación del pedido #{self.pedido_id}"
