from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from vehiculos.models import Auto
from .models import Reserva, PagoSimulado
from .forms import ReservaForm, PagoSimuladoForm
from django.contrib.auth.decorators import login_required

def crear_reserva(request, auto_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Debés iniciar sesión o registrarte para poder reservar.")
        return redirect('login')
    auto = get_object_or_404(Auto, id=auto_id)
    
    if request.method == 'POST':
        form = ReservaForm(request.POST, auto=auto)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.vehiculo = auto
            reserva.save()
            # Redirigimos al pago
            return redirect('reservas:pagar_reserva', reserva_id=reserva.id)
    else:
        form = ReservaForm(auto=auto)
    
    return render(request, 'reservas/crear_reserva.html', {
        'form': form,
        'usuario': request.user,
        'auto': auto,
        'precio_por_dia': auto.precio_por_dia,
    })
    
@login_required
def pagar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    # Monto calculado
    monto = reserva.vehiculo.precio_por_dia * (reserva.fecha_fin - reserva.fecha_inicio).days

    if request.method == 'POST':
        post = request.POST.copy()
        post['monto'] = str(monto)  # Aseguramos que el campo "monto" esté presente
        form = PagoSimuladoForm(post)

        if form.is_valid():
            numero = form.cleaned_data['numero_tarjeta']

            # Validación ficticia: si termina en 0000, rechazamos
            if numero.endswith('0000'):
                messages.error(request, "El pago fue rechazado: tarjeta inválida.")
            else:
                # Guardamos el pago simulado exitoso
                PagoSimulado.objects.create(
                    reserva=reserva,
                    nombre_en_tarjeta=form.cleaned_data['nombre_en_tarjeta'],
                    numero_tarjeta=numero,
                    vencimiento=form.cleaned_data['vencimiento'],
                    codigo_seguridad=form.cleaned_data['codigo_seguridad'],
                    monto=monto,
                    estado='exitoso'
                )

                # Confirmamos la reserva
                reserva.estado = 'confirmada'
                reserva.save()

                return redirect('reservas:reserva_exitosa', reserva_id=reserva.id)
        # Si no es válido, dejamos que llegue al render final con errores
    else:
        form = PagoSimuladoForm(initial={'monto': monto})

    return render(request, 'reservas/pagar_reserva.html', {
        'form': form,
        'reserva': reserva,
        'monto': monto
    })

def reserva_exitosa(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    return render(request, 'reservas/reserva_exitosa.html', {
        'reserva': reserva
    })