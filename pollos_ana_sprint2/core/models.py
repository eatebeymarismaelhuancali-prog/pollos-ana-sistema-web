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
 def __str__(self): return f'Venta #{self.pk}'
class DetalleVenta(models.Model):
 venta=models.ForeignKey(Venta,on_delete=models.CASCADE,related_name='detalles')
 producto=models.ForeignKey(Producto,on_delete=models.PROTECT)
 cantidad=models.PositiveIntegerField()
 precio_unitario=models.DecimalField(max_digits=10,decimal_places=2)
 subtotal=models.DecimalField(max_digits=12,decimal_places=2)
class Pedido(models.Model):
 CANALES=[('presencial','Presencial'),('telefono','Teléfono'),('whatsapp','WhatsApp')]
 ESTADOS=[('pendiente','Pendiente'),('preparacion','En preparación'),('listo','Listo'),('finalizado','Finalizado')]
 venta=models.OneToOneField(Venta,on_delete=models.PROTECT,related_name='pedido')
 canal=models.CharField(max_length=20,choices=CANALES)
 cliente=models.CharField(max_length=120,blank=True)
 observaciones=models.TextField(blank=True)
 estado=models.CharField(max_length=20,choices=ESTADOS,default='pendiente')
 creado=models.DateTimeField(auto_now_add=True)
