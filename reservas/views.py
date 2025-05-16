from django.shortcuts import get_object_or_404, render, redirect
from vehiculos.models import Auto
from .forms import ReservaForm
from django.contrib.auth.decorators import login_required

@login_required
def crear_reserva(request, auto_id):
    auto = get_object_or_404(Auto, pk=auto_id)
    if request.method == 'POST':
        form = ReservaForm(request.POST, auto=auto)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.vehiculo = auto  # Fijar explícitamente el vehículo
            reserva.save()
            return redirect('reserva_exitosa')
    else:
        form = ReservaForm(auto=auto)
    return render(request, 'reservas/crear_reserva.html', {
        'form': form,
        'usuario': request.user,
        'auto': auto,
        'precio_por_dia': auto.precio_por_dia,
    })

def reserva_exitosa(request):
    return render(request, 'reservas/reserva_exitosa.html')