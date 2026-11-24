import json
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models import F
from django.utils import timezone
from decimal import InvalidOperation
from .models import (
    Producto, Categoria, Venta, DetalleVenta,
    Pedido, Caja, MovimientoCaja
)
from .forms import ProductoForm,CategoriaForm
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from io import BytesIO

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

  messages.success(
      request,
      f'Venta #{venta.id} registrada correctamente por Bs {total}'
  )
  return redirect('comprobante_venta', pk=venta.id)

 except (ValueError, KeyError, TypeError,
         OverflowError, json.JSONDecodeError) as e:
  messages.error(
      request,
      f'No se pudo registrar: {e}'
  )

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

# ========================================
# MÓDULO DE CAJA - POLLOS ANA
# ========================================

def obtener_caja_abierta():
    return Caja.objects.filter(
        estado='abierta'
    ).order_by('-fecha_apertura').first()


def calcular_efectivo_esperado(caja):
    ingresos = MovimientoCaja.objects.filter(
        caja=caja,
        tipo='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    egresos = MovimientoCaja.objects.filter(
        caja=caja,
        tipo='egreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    ventas_efectivo = Venta.objects.filter(
        caja=caja,
        metodo_pago='efectivo'
    ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')

    return caja.monto_inicial + ingresos + ventas_efectivo - egresos


@login_required
def caja(request):
    caja_actual = obtener_caja_abierta()

    movimientos = []
    efectivo_esperado = Decimal('0.00')
    ventas_caja = []

    if caja_actual:
        movimientos = MovimientoCaja.objects.filter(
            caja=caja_actual
        ).select_related('usuario').order_by('-fecha')

        ventas_caja = Venta.objects.filter(
            caja=caja_actual
        ).order_by('-fecha')

        efectivo_esperado = calcular_efectivo_esperado(
            caja_actual
        )

    return render(request, 'core/caja.html', {
        'caja_actual': caja_actual,
        'movimientos': movimientos,
        'ventas_caja': ventas_caja,
        'efectivo_esperado': efectivo_esperado,
    })


def validar_monto(valor, permitir_cero=False):
    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('El monto ingresado no es válido.')

    if not monto.is_finite():
        raise ValueError('El monto debe ser finito.')

    if monto < 0 or (monto == 0 and not permitir_cero):
        raise ValueError('El monto debe ser mayor a cero.')

    if monto.as_tuple().exponent < -2:
        raise ValueError('Utiliza máximo dos decimales.')

    if monto >= Decimal('10000000000'):
        raise ValueError('El monto supera el límite permitido.')

    return monto


@login_required
@require_POST
def abrir_caja(request):
    if not gestor(request.user):
        return HttpResponseForbidden('Solo administrador')

    try:
        monto = validar_monto(
            request.POST.get('monto_inicial'),
            permitir_cero=True
        )

        # Bloqueo de aperturas simultáneas:
        # para producción debe reforzarse con una
        # restricción de base de datos.
        with transaction.atomic():
            if Caja.objects.filter(estado='abierta').exists():
                raise ValueError('Ya existe una caja abierta.')

            Caja.objects.create(
                usuario_apertura=request.user,
                monto_inicial=monto,
                estado='abierta'
            )

        messages.success(
            request,
            'Caja abierta correctamente.'
        )

    except ValueError as error:
        messages.error(request, str(error))

    return redirect('caja')


@login_required
@require_POST
def registrar_movimiento_caja(request):
    if not gestor(request.user):
        return HttpResponseForbidden('Solo administrador')

    try:
        tipo = request.POST.get('tipo')
        concepto = request.POST.get('concepto', '').strip()
        monto = validar_monto(request.POST.get('monto'))

        if tipo not in ('ingreso', 'egreso'):
            raise ValueError('Tipo de movimiento inválido.')

        if not concepto:
            raise ValueError('Debes indicar el concepto.')

        with transaction.atomic():
            caja_actual = Caja.objects.select_for_update().filter(
                estado='abierta'
            ).first()

            if not caja_actual:
                raise ValueError('No existe una caja abierta.')

            if tipo == 'egreso':
                disponible = calcular_efectivo_esperado(
                    caja_actual
                )

                if monto > disponible:
                    raise ValueError(
                        'El egreso supera el efectivo disponible.'
                    )

            MovimientoCaja.objects.create(
                caja=caja_actual,
                tipo=tipo,
                concepto=concepto[:200],
                monto=monto,
                usuario=request.user
            )

        messages.success(
            request,
            'Movimiento registrado correctamente.'
        )

    except ValueError as error:
        messages.error(request, str(error))

    return redirect('caja')


@login_required
@require_POST
def cerrar_caja(request):
    if not gestor(request.user):
        return HttpResponseForbidden('Solo administrador')

    try:
        contado = validar_monto(
            request.POST.get('monto_contado'),
            permitir_cero=True
        )

        with transaction.atomic():
            caja_actual = Caja.objects.select_for_update().filter(
                estado='abierta'
            ).first()

            if not caja_actual:
                raise ValueError('No existe una caja abierta.')

            esperado = calcular_efectivo_esperado(
                caja_actual
            )

            caja_actual.monto_esperado = esperado
            caja_actual.monto_contado = contado
            caja_actual.diferencia = contado - esperado
            caja_actual.usuario_cierre = request.user
            caja_actual.fecha_cierre = timezone.now()
            caja_actual.estado = 'cerrada'

            caja_actual.save()

        messages.success(
            request,
            'Caja cerrada correctamente.'
        )

    except ValueError as error:
        messages.error(request, str(error))

    return redirect('caja')


@login_required
def comprobante_venta(request, pk):
    venta = get_object_or_404(
        Venta.objects.select_related(
            'usuario',
            'pedido'
        ).prefetch_related(
            'detalles__producto'
        ),
        pk=pk
    )

    return render(
        request,
        'core/comprobante_venta.html',
        {
            'venta': venta,
            'pedido': venta.pedido,
            'detalles': venta.detalles.all(),
        }
    )


@login_required
def descargar_nota_pdf(request, pk):
    from io import BytesIO
    from pathlib import Path

    from django.conf import settings
    from django.http import HttpResponse
    from django.shortcuts import get_object_or_404
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader, simpleSplit

    venta = get_object_or_404(
        Venta.objects.select_related(
            'usuario', 'pedido'
        ).prefetch_related(
            'detalles__producto'
        ),
        pk=pk
    )

    pedido = venta.pedido
    detalles = list(venta.detalles.all())

    # Medidas en puntos PDF (72 puntos = 1 pulgada).
    # 80 mm de ancho y márgenes de 4 mm.
    MM = 72 / 25.4
    ancho = 80 * MM
    margen = 4 * MM
    ancho_util = ancho - 2 * margen

    # Calcular la altura necesaria según los productos.
    altura = 390 + len(detalles) * 65
    altura = max(altura, 480)

    buffer = BytesIO()
    pdf = canvas.Canvas(
        buffer,
        pagesize=(ancho, altura)
    )

    y = altura - 20

    def escribir(texto, tamano=9, negrita=False,
                 centrado=False, espacio=4):
        nonlocal y

        fuente = (
            "Helvetica-Bold"
            if negrita else "Helvetica"
        )

        pdf.setFont(fuente, tamano)

        lineas = simpleSplit(
            str(texto),
            fuente,
            tamano,
            ancho_util
        )

        for linea in lineas:
            if centrado:
                pdf.drawCentredString(
                    ancho / 2, y, linea
                )
            else:
                pdf.drawString(margen, y, linea)

            y -= tamano + espacio

    def separador():
        nonlocal y
        y -= 4
        pdf.setDash(2, 2)
        pdf.line(margen, y, ancho - margen, y)
        pdf.setDash()
        y -= 13

    # LOGO DE POLLOS ANA
    ruta_logo = (
        Path(settings.BASE_DIR)
        / 'core'
        / 'static'
        / 'core'
        / 'img'
        / 'logo.jpg'
    )

    if ruta_logo.exists():
        try:
            imagen = ImageReader(str(ruta_logo))
            iw, ih = imagen.getSize()

            max_ancho = 70
            max_alto = 65
            escala = min(
                max_ancho / iw,
                max_alto / ih
            )

            logo_ancho = iw * escala
            logo_alto = ih * escala

            pdf.drawImage(
                imagen,
                (ancho - logo_ancho) / 2,
                y - logo_alto,
                width=logo_ancho,
                height=logo_alto,
                mask='auto'
            )

            y -= logo_alto + 12
        except Exception:
            pass


    escribir(
        "NOTA DE VENTA",
        10,
        negrita=True,
        centrado=True
    )

    separador()

    escribir(
        f"VENTA Nro.: {venta.id:06d}",
        9,
        negrita=True
    )

    escribir(
        f"FECHA: {venta.fecha:%d/%m/%Y %H:%M}"
    )

    escribir(
        f"CAJERO: {venta.usuario.username}"
    )

    escribir(
        f"CLIENTE: {pedido.cliente or 'Consumidor final'}"
    )

    escribir(
        f"PEDIDO: {pedido.get_canal_display()}"
    )

    separador()

    escribir(
        "DETALLE DE PRODUCTOS",
        9,
        negrita=True,
        centrado=True
    )

    y -= 6

    # Productos de la venta.
    for detalle in detalles:
        escribir(
            detalle.producto.nombre,
            9,
            negrita=True
        )

        cantidad = detalle.cantidad
        precio = detalle.precio_unitario
        subtotal = detalle.subtotal

        texto_izquierda = (
            f"{cantidad} x Bs {precio}"
        )

        texto_derecha = f"Bs {subtotal}"

        pdf.setFont("Helvetica", 9)

        pdf.drawString(
            margen + 5,
            y,
            texto_izquierda
        )

        pdf.drawRightString(
            ancho - margen,
            y,
            texto_derecha
        )

        y -= 22

    separador()

    pdf.setFont("Helvetica-Bold", 13)

    pdf.drawString(
        margen,
        y,
        "TOTAL:"
    )

    pdf.drawRightString(
        ancho - margen,
        y,
        f"Bs {venta.total}"
    )

    y -= 25

    escribir(
        f"PAGO: {venta.get_metodo_pago_display()}"
    )

    separador()

    escribir(
        "GRACIAS POR SU PREFERENCIA!",
        9,
        negrita=True,
        centrado=True
    )

    escribir(
        "POLLOS ANA",
        10,
        negrita=True,
        centrado=True
    )

    y -= 8


    escribir(
        "No valido como factura fiscal, PROXIMO SPRINT",
        7,
        centrado=True
    )

    pdf.save()
    buffer.seek(0)

    respuesta = HttpResponse(
        buffer.getvalue(),
        content_type='application/pdf'
    )

    respuesta['Content-Disposition'] = (
        f'attachment; filename="'
        f'Nota_Venta_Pollos_Ana_{venta.id}.pdf"'
    )

    return respuesta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def mapa_calor(request):
    return render(
        request,
        'core/mapa_calor.html'
    )

