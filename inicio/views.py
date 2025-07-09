from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from sucursales.models import Sucursal
from vehiculos.models import Auto, CATEGORIAS
from reservas.models import Reserva
from django.db.models import Q
from django.core.mail import send_mail
from django.http import HttpResponse

def index(request):
    if request.user.is_authenticated and request.user.groups.filter(name='admin').exists():
        return redirect('panel_admin')
    elif request.user.is_authenticated and request.user.groups.filter(name='empleado').exists():
        return redirect('panel_empleado')


    sucursales = Sucursal.objects.all()
    autos = Auto.objects.select_related('sucursal').filter(activo=True)
    buscar       = request.GET.get('buscar', '')
    fecha_desde  = request.GET.get('fecha_desde', '')
    fecha_hasta  = request.GET.get('fecha_hasta', '')
    orden        = request.GET.get('orden', '')
    sucursal_id  = request.GET.get('sucursal', '')
    categoria    = request.GET.get('categoria', '')

    # Filtrar por categoría
    if categoria:
        autos = autos.filter(categoria=categoria)

    # Filtrar por texto
    if buscar:
        autos = autos.filter(Q(marca__icontains=buscar) | Q(modelo__icontains=buscar))

    # Filtrar por sucursal
    if sucursal_id:
        autos = autos.filter(sucursal__id=sucursal_id)

    # Filtrar por rango de fechas **solo si ambas están**
    if (fecha_desde and not fecha_hasta) or (fecha_hasta and not fecha_desde):
        messages.warning(request, "Debés seleccionar ambas fechas para filtrar por rango.")
    if fecha_desde and fecha_hasta:
        autos = autos.exclude(
            reserva__fecha_inicio__lte=fecha_hasta,
            reserva__fecha_fin__gte=fecha_desde
        )

    # Ordenar por precio
    if orden == 'menor':
        autos = autos.order_by('precio_por_dia')
    elif orden == 'mayor':
        autos = autos.order_by('-precio_por_dia')

    es_admin = request.user.groups.filter(name='admin').exists()

    return render(request, "index.html", {
        "sucursales": sucursales,
        "autos": autos,
        "categorias": CATEGORIAS,
        "request": request,            # para el template
        "es_admin": es_admin,
        "fecha_desde": fecha_desde,    # pasamos al template
        "fecha_hasta": fecha_hasta,
    })



def detalle_auto(request, auto_id):
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    if fecha_desde and fecha_hasta:
        request.session['fecha_desde'] = fecha_desde
        request.session['fecha_hasta'] = fecha_hasta
    else:
        request.session.pop('fecha_desde', None)
        request.session.pop('fecha_hasta', None)

    auto = get_object_or_404(Auto, pk=auto_id, activo=True)
    reservar_url = reverse('reservas:crear_reserva', args=[auto.id])
    if fecha_desde and fecha_hasta:
        reservar_url += f'?fecha_desde={fecha_desde}&fecha_hasta={fecha_hasta}'

    return render(request, 'detalle_auto.html', {
        'auto':          auto,
        'reservar_url':  reservar_url,
    })



from usuarios.forms import UserEditForm


@login_required
def editar_perfil(request):
    """Vista para editar el perfil del usuario."""
    if request.method == 'POST':
        # Procesar el formulario enviado
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('perfil')
    else:
        # Mostrar formulario con datos actuales
        form = UserEditForm(instance=request.user)
    
    return render(request, 'inicio/editar_perfil.html', {
        'form': form
    })

@login_required
def perfil(request):
    """Vista para mostrar el perfil del usuario."""
    es_admin = request.user.groups.filter(name='admin').exists()
    return render(request, 'inicio/perfil.html', {
        'user': request.user,
        'es_admin': es_admin
    })

@login_required
def historial_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha_inicio') 
    
    return render(request, 'inicio/historial_reservas.html', {
        'reservas': reservas
    })
    
@login_required
def detalle_reserva(request, reserva_id):
    # Obtiene la reserva que pertenece al usuario actual o 404 si no existe
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    return render(request, 'inicio/detalle_reserva.html', {'reserva': reserva})

