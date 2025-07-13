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
        reservas = Reserva.objects.all()
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
                if not datos['vehiculos_mas_alquilados']['labels']:
                    datos['vehiculos_mas_alquilados'] = {'labels': [], 'data': []}

            # Dinero recaudado por vehículo
            if 'dinero_por_vehiculo' in tipos:
                dinero_por_vehiculo = {}
                for reserva in reservas:
                    modelo = reserva.vehiculo.modelo
                    dias = (reserva.fecha_fin - reserva.fecha_inicio).days
                    monto = dias * float(reserva.vehiculo.precio_por_dia)
                    dinero_por_vehiculo[modelo] = dinero_por_vehiculo.get(modelo, 0) + monto
                datos['dinero_por_vehiculo'] = {
                    'labels': list(dinero_por_vehiculo.keys()),
                    'data': list(dinero_por_vehiculo.values())
                }
                if not datos['dinero_por_vehiculo']['labels']:
                    datos['dinero_por_vehiculo'] = {'labels': [], 'data': []}

            # Cantidad de vehículos alquilados por sucursal
            if 'vehiculos_por_sucursal' in tipos:
                sucursal = reservas.values('vehiculo__sucursal__nombre').annotate(total=Count('vehiculo')).order_by('-total')
                datos['vehiculos_por_sucursal'] = {
                    'labels': [item['vehiculo__sucursal__nombre'] for item in sucursal],
                    'data': [item['total'] for item in sucursal]
                }
                if not datos['vehiculos_por_sucursal']['labels']:
                    datos['vehiculos_por_sucursal'] = {'labels': [], 'data': []}

            # Dinero recaudado por sucursal
            if 'dinero_por_sucursal' in tipos:
                dinero_por_sucursal = {}
                for reserva in reservas:
                    sucursal = getattr(reserva.vehiculo.sucursal, 'nombre', 'Sin sucursal')
                    dias = (reserva.fecha_fin - reserva.fecha_inicio).days
                    monto = dias * float(reserva.vehiculo.precio_por_dia)
                    dinero_por_sucursal[sucursal] = dinero_por_sucursal.get(sucursal, 0) + monto
                datos['dinero_por_sucursal'] = {
                    'labels': list(dinero_por_sucursal.keys()),
                    'data': list(dinero_por_sucursal.values())
                }
                if not datos['dinero_por_sucursal']['labels']:
                    datos['dinero_por_sucursal'] = {'labels': [], 'data': []}

            # Cantidad de vehículos alquilados por usuario
            if 'vehiculos_por_usuario' in tipos:
                usuario = reservas.values(
                    'usuario__email',
                    'usuario__nombre',
                    'usuario__apellido'
                ).annotate(total=Count('vehiculo')).order_by('-total')
                
                datos['vehiculos_por_usuario'] = {
                    'labels': [f"{item['usuario__nombre']} {item['usuario__apellido']}" 
                              if item['usuario__nombre'] and item['usuario__apellido']
                              else item['usuario__email'] for item in usuario],
                    'data': [item['total'] for item in usuario]
                }
                if not datos['vehiculos_por_usuario']['labels']:
                    datos['vehiculos_por_usuario'] = {'labels': [], 'data': []}

            # Dinero recaudado por usuario
            if 'dinero_por_usuario' in tipos:
                dinero_por_usuario = {}
                for reserva in reservas:
                    usuario = reserva.usuario
                    if usuario.nombre and usuario.apellido:
                        nombre_usuario = f"{usuario.nombre} {usuario.apellido}"
                    else:
                        nombre_usuario = usuario.email or usuario.username
                        
                    dias = (reserva.fecha_fin - reserva.fecha_inicio).days
                    monto = dias * float(reserva.vehiculo.precio_por_dia)
                    dinero_por_usuario[nombre_usuario] = dinero_por_usuario.get(nombre_usuario, 0) + monto
                
                dinero_por_usuario = dict(sorted(dinero_por_usuario.items(), 
                                               key=lambda x: x[1], 
                                               reverse=True))
                
                datos['dinero_por_usuario'] = {
                    'labels': list(dinero_por_usuario.keys()),
                    'data': list(dinero_por_usuario.values())
                }

    return render(request, "vehiculos_graficos/graficos.html", {"form": form, "datos": datos, "mensaje": mensaje})
