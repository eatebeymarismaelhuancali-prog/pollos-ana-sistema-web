import json
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from .models import Producto,Categoria,Venta,DetalleVenta,Pedido
from .forms import ProductoForm,CategoriaForm

def gestor(user): return user.is_staff or user.is_superuser
@login_required
def dashboard(request):
 return render(request,'core/dashboard.html',{'productos':Producto.objects.count(),'ventas':Venta.objects.count(),'pedidos':Pedido.objects.exclude(estado='finalizado').count(),'total':Venta.objects.aggregate(t=Sum('total'))['t'] or 0})
@login_required
def productos(request):
 return render(request,'core/productos.html',{'productos':Producto.objects.select_related('categoria').all(),'categorias':Categoria.objects.all()})
@login_required
def categoria_nueva(request):
 if not gestor(request.user): return HttpResponseForbidden('Solo administrador')
 form=CategoriaForm(request.POST or None)
 if request.method=='POST' and form.is_valid():form.save();messages.success(request,'Categoría creada');return redirect('productos')
 return render(request,'core/form.html',{'form':form,'titulo':'Nueva categoría'})
@login_required
def producto_editar(request,pk=None):
 if not gestor(request.user): return HttpResponseForbidden('Solo administrador')
 obj=get_object_or_404(Producto,pk=pk) if pk else None
 form=ProductoForm(request.POST or None,request.FILES or None,instance=obj)
 if request.method=='POST' and form.is_valid():form.save();messages.success(request,'Producto guardado');return redirect('productos')
 return render(request,'core/form.html',{'form':form,'titulo':'Editar producto' if obj else 'Nuevo producto'})
@login_required
def pos(request):
 return render(request,'core/pos.html',{'productos':Producto.objects.filter(activo=True).select_related('categoria'),'categorias':Categoria.objects.all()})
@login_required
@require_POST
def registrar_venta(request):
 try:
  data=json.loads(request.body)
  items=data['items']
  if not isinstance(items,list) or not items or len(items)>100: raise ValueError('Carrito inválido')
  canal=data.get('canal','presencial');metodo=data.get('metodo','efectivo')
  if canal not in dict(Pedido.CANALES) or metodo not in dict(Venta.METODOS): raise ValueError('Opción inválida')
  cantidades={}
  for item in items:
   pid=int(item['id']);cantidad=int(item['cantidad'])
   if cantidad<1 or cantidad>100:raise ValueError('Cantidad inválida')
   cantidades[pid]=cantidades.get(pid,0)+cantidad
  if any(q>100 for q in cantidades.values()):raise ValueError('Cantidad inválida')
  productos={p.id:p for p in Producto.objects.filter(id__in=cantidades,activo=True)}
  if len(productos)!=len(cantidades):raise ValueError('Producto no disponible')
  total=sum((p.precio*cantidades[p.id] for p in productos.values()),Decimal('0'))
  with transaction.atomic():
   venta=Venta.objects.create(usuario=request.user,total=total,metodo_pago=metodo)
   DetalleVenta.objects.bulk_create([DetalleVenta(venta=venta,producto=p,cantidad=cantidades[p.id],precio_unitario=p.precio,subtotal=p.precio*cantidades[p.id]) for p in productos.values()])
   Pedido.objects.create(venta=venta,canal=canal,cliente=str(data.get('cliente',''))[:120],observaciones=str(data.get('observaciones',''))[:1000])
  messages.success(request,f'Venta #{venta.id} registrada por Bs {total}')
 except (ValueError,KeyError,TypeError,OverflowError,json.JSONDecodeError) as e:messages.error(request,f'No se pudo registrar: {e}')
 return redirect('pos')
@login_required
def cocina(request):
 return render(request,'core/cocina.html',{'pedidos':Pedido.objects.select_related('venta').prefetch_related('venta__detalles__producto').order_by('-creado')[:80]})
@login_required
@require_POST
def estado_pedido(request,pk):
 pedido=get_object_or_404(Pedido,pk=pk)
 orden=['pendiente','preparacion','listo','finalizado']
 if pedido.estado!='finalizado':pedido.estado=orden[orden.index(pedido.estado)+1];pedido.save(update_fields=['estado'])
 return redirect('cocina')
@login_required
def ventas(request):
 return render(request,'core/ventas.html',{'ventas':Venta.objects.select_related('usuario').prefetch_related('detalles__producto').order_by('-fecha')[:100]})
