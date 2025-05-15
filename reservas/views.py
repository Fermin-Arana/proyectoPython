from django.shortcuts import render, redirect
from .forms import ReservaForm
from .models import Reserva
from django.contrib.auth.decorators import login_required

@login_required
def crear_reserva(request):
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.save()
            return redirect('reserva_exitosa') 
    else:
        form = ReservaForm()
    return render(request, 'reservas/crear_reserva.html', {'form': form})

def reserva_exitosa(request):
    return render(request, 'reservas/reserva_exitosa.html')