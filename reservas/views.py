from datetime import datetime
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from usuarios.models import Usuario
from vehiculos.models import Auto
from .models import Reserva, PagoSimulado, Tarjeta
from .forms import ReservaForm, PagoSimuladoForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings


def crear_reserva(request, auto_id, reserva_id = None):
    if not request.user.is_authenticated:
        messages.warning(request, "Debés iniciar sesión o registrarte para poder reservar.")
        return redirect('login')
    auto = get_object_or_404(Auto, id=auto_id)
    reserva = None
    # Leer las fechas de la sesión
    sd = request.session.get('fecha_desde')
    sh = request.session.get('fecha_hasta')
    
    # Parsear a date de forma segura
    fecha_desde = None
    fecha_hasta = None
    if sd and sh:
        try:
            fecha_desde = datetime.strptime(sd, "%Y-%m-%d").date()
            fecha_hasta = datetime.strptime(sh, "%Y-%m-%d").date()
        except ValueError:
            # Si el formato es inválido, las dejamos en None
            fecha_desde = fecha_hasta = None
    if reserva_id:
        reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
        
    if request.method == 'POST':
        if reserva:  
            form = ReservaForm(request.POST, auto=auto, instance=reserva)
        else:
            form = ReservaForm(request.POST, auto=auto)

        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.vehiculo = auto

            if not reserva_id:
                # Solo usar fechas de sesión si es una nueva reserva
                if fecha_desde and fecha_hasta:
                    reserva.fecha_inicio = fecha_desde
                    reserva.fecha_fin = fecha_hasta

            reserva.save()
            return redirect('reservas:pagar_reserva', reserva_id=reserva.id)
    else:
        form = ReservaForm(auto=auto, initial={
            'fecha_inicio': fecha_desde.isoformat() if fecha_desde else '',
            'fecha_fin': fecha_hasta.isoformat() if fecha_hasta else '',
        })

    return render(request, 'reservas/crear_reserva.html', {
        'form':           form,
        'usuario':        request.user,
        'auto':           auto,
        'precio_por_dia': auto.precio_por_dia,
        'fecha_desde':    sd,
        'fecha_hasta':    sh,
    })
    
@login_required
def pagar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    # Monto calculado
    dias = (reserva.fecha_fin - reserva.fecha_inicio).days
    monto = reserva.vehiculo.precio_por_dia * dias
    
    

    if request.method == 'POST':
        post = request.POST.copy()
        post['monto'] = str(monto)
        form = PagoSimuladoForm(post)

        if form.is_valid():
            datos = form.cleaned_data

            try:
                tarjeta = Tarjeta.objects.get(
                    nombre_en_tarjeta=datos['nombre_en_tarjeta'],
                    numero_tarjeta=datos['numero_tarjeta'],
                    vencimiento=datos['vencimiento'],
                    codigo_seguridad=datos['codigo_seguridad']
                )
            except Tarjeta.DoesNotExist:
                messages.error(request, "Datos de tarjeta incorrectos o tarjeta no registrada.")
            else:
                if tarjeta.saldo < monto:
                    messages.error(request, "La tarjeta no tiene saldo suficiente.")
                else:
                    # Descontamos saldo
                    tarjeta.saldo -= monto
                    tarjeta.save()

                    # Creamos el pago exitoso
                    PagoSimulado.objects.create(
                        reserva=reserva,
                        tarjeta=tarjeta,
                        monto=monto,
                        estado='exitoso'
                    )

                    reserva.estado = 'confirmada'
                    reserva.save()
                    send_mail(
                        subject='Reserva Confirmada - Alquileres María',
                        message = f"""\
                        Hola {request.user.nombre or request.user.username},

                        Tu reserva para el vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo}
                        ha sido confirmada exitosamente.

                        Detalles:
                        - Fecha de inicio: {reserva.fecha_inicio}
                        - Fecha de fin: {reserva.fecha_fin}
                        - Monto pagado: ${monto:.2f}

                        ¡Gracias por confiar en nosotros!

                        Atentamente,
                        El equipo de Alquileres María
                        """,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[request.user.correo],
                            fail_silently=False,
                    )
                    if not request.user.email:
                        messages.warning(request, "No se pudo enviar el correo porque no tenés un email registrado.")
                    return redirect('reservas:reserva_exitosa', reserva_id=reserva.id)
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

@login_required
def reserva_cancelar(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    if request.method == 'POST':
        reserva.estado = 'cancelada'
        reserva.save()
        messages.success(request, "Reserva cancelada exitosamente.")
        return redirect('reservas:reserva_cancelada')
    return render(request, 'reservas/reserva_cancelar.html', {'reserva': reserva})

def reserva_cancelada(request):
    return render(request, 'reservas/reserva_cancelada.html')

@login_required
def reserva_modificar(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    auto = reserva.vehiculo

    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva, auto=auto)
        if form.is_valid():
            form.save()
            messages.success(request, "Reserva modificada exitosamente.")
            return redirect('historial_reservas') 
    else:
        form = ReservaForm(instance=reserva, auto=auto)

    return render(request, 'reservas/reserva_modificar.html', {
        'form': form,
        'auto': auto,
        'reserva': reserva
    })