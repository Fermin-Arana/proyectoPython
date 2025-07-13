from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from reservas.models import Reserva
from django.db.models import Count
from .forms import FiltroGraficoForm
from django.db import models

def es_admin(user):
    return user.is_authenticated and user.groups.filter(name='admin').exists()

@user_passes_test(es_admin)
def autos_mas_alquilados(request):
    datos = {}
    mensaje = None
    form = FiltroGraficoForm(request.GET or None)
    if form.is_valid():
        fecha_inicio = form.cleaned_data['fecha_inicio']
        fecha_fin = form.cleaned_data['fecha_fin']
        tipos = form.cleaned_data['tipo_grafico']
        reservas = Reserva.objects.filter(fecha_inicio__gte=fecha_inicio, fecha_fin__lte=fecha_fin)
        if not reservas.exists():
            mensaje = "No hay datos disponibles"
        else:
            # Vehículos más alquilados
            if 'vehiculos_mas_alquilados' in tipos:
                conteo = reservas.values('vehiculo__modelo').annotate(total=Count('vehiculo')).order_by('-total')
                datos['vehiculos_mas_alquilados'] = {
                    'labels': [item['vehiculo__modelo'] for item in conteo],
                    'data': [item['total'] for item in conteo]
                }
            # Dinero recaudado por vehículo
            if 'dinero_por_vehiculo' in tipos:
                dinero = reservas.values('vehiculo__modelo').annotate(
                    total=models.Sum(models.F('vehiculo__precio_por_dia') * (models.F('fecha_fin') - models.F('fecha_inicio')))
                )
                datos['dinero_por_vehiculo'] = {
                    'labels': [item['vehiculo__modelo'] for item in dinero],
                    'data': [float(item['total'].days if hasattr(item['total'], 'days') else item['total'] or 0) for item in dinero]
                }
            # Cantidad de vehículos alquilados por sucursal
            if 'vehiculos_por_sucursal' in tipos:
                sucursal = reservas.values('vehiculo__sucursal__nombre').annotate(total=Count('vehiculo')).order_by('-total')
                datos['vehiculos_por_sucursal'] = {
                    'labels': [item['vehiculo__sucursal__nombre'] for item in sucursal],
                    'data': [item['total'] for item in sucursal]
                }
            # Dinero recaudado por sucursal
            if 'dinero_por_sucursal' in tipos:
                dinero_suc = reservas.values('vehiculo__sucursal__nombre').annotate(
                    total=models.Sum(models.F('vehiculo__precio_por_dia') * (models.F('fecha_fin') - models.F('fecha_inicio')))
                )
                datos['dinero_por_sucursal'] = {
                    'labels': [item['vehiculo__sucursal__nombre'] for item in dinero_suc],
                    'data': [float(item['total'].days if hasattr(item['total'], 'days') else item['total'] or 0) for item in dinero_suc]
                }
            # Cantidad de vehículos alquilados por usuario
            if 'vehiculos_por_usuario' in tipos:
                usuario = reservas.values('usuario__email').annotate(total=Count('vehiculo')).order_by('-total')
                datos['vehiculos_por_usuario'] = {
                    'labels': [item['usuario__email'] for item in usuario],
                    'data': [item['total'] for item in usuario]
                }
            # Dinero recaudado por usuario
            if 'dinero_por_usuario' in tipos:
                dinero_usr = reservas.values('usuario__email').annotate(
                    total=models.Sum(models.F('vehiculo__precio_por_dia') * (models.F('fecha_fin') - models.F('fecha_inicio')))
                )
                datos['dinero_por_usuario'] = {
                    'labels': [item['usuario__email'] for item in dinero_usr],
                    'data': [float(item['total'].days if hasattr(item['total'], 'days') else item['total'] or 0) for item in dinero_usr]
                }
    return render(request, "vehiculos_graficos/graficos.html", {"form": form, "datos": datos, "mensaje": mensaje})
