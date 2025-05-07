from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from sucursales.models import Sucursal
from vehiculos.models import Auto
from usuarios.models import Usuario
from django.db.models import Q

# Create your views here.
def index(request):
    sucursales = Sucursal.objects.all()
    autos = Auto.objects.select_related('sucursal').all()

    buscar = request.GET.get('buscar', '')
    fecha = request.GET.get('fecha', '')
    orden = request.GET.get('orden', '')
    sucursal_id = request.GET.get('sucursal', '')

    # Filtro por texto
    if buscar:
        autos = autos.filter(Q(marca__icontains=buscar) | Q(modelo__icontains=buscar))

    # Filtro por sucursal seleccionada
    if sucursal_id:
        autos = autos.filter(sucursal__id=sucursal_id)

    # Filtro por fecha (excluir autos ya reservados ese día)
    if fecha:
        autos = autos.exclude(reserva__fecha_inicio__lte=fecha, reserva__fecha_fin__gte=fecha)

    # Ordenar por precio
    if orden == 'menor':
        autos = autos.order_by('precio_por_dia')
    elif orden == 'mayor':
        autos = autos.order_by('-precio_por_dia')

    return render(request, "index.html", {
        "sucursales": sucursales,
        "autos": autos,
        "request": request  # Para acceder a los valores en la plantilla
    })



def detalle_auto(request, auto_id):
    # Obtener el auto seleccionado
    auto = get_object_or_404(Auto, id=auto_id)

    return render(request, "vehiculos/detalle_auto.html", {"auto": auto})