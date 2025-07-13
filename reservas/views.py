from datetime import datetime, timedelta
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from usuarios.models import Usuario
from vehiculos.models import Auto
from .models import Reserva, PagoSimulado, Tarjeta
from .forms import ReservaForm, PagoSimuladoForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.conf import settings
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone


def crear_reserva(request, auto_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Debés iniciar sesión o registrarte para poder reservar.")
        return redirect('usuarios:login')
    auto = get_object_or_404(Auto, id=auto_id, activo=True)
    
    # Leer fechas desde parámetros GET primero, luego desde sesión
    fecha_desde = request.GET.get('fecha_desde') or request.session.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta') or request.session.get('fecha_hasta')
    
    # Actualizar sesión si las fechas vienen por GET
    if request.GET.get('fecha_desde') and request.GET.get('fecha_hasta'):
        request.session['fecha_desde'] = request.GET.get('fecha_desde')
        request.session['fecha_hasta'] = request.GET.get('fecha_hasta')

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
    
    # Eliminar estas líneas problemáticas ya que reserva_id no está definido
    # if reserva_id:
    #     reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
        
    if request.method == 'POST':
        if reserva:  
            form = ReservaForm(request.POST, auto=auto, instance=reserva)
        else:
            form = ReservaForm(request.POST, auto=auto)

        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.vehiculo = auto

            # Cambiar esta condición ya que reserva_id no existe
            if not reserva.pk:  # Si es una nueva reserva (no tiene primary key)
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

    if reserva.estado == 'cancelada':
        messages.info(request, "Esta reserva ya fue cancelada.")
        return redirect('historial_reservas')  

    try:
        pago = reserva.pagosimulado  
    except PagoSimulado.DoesNotExist:
        pago = None

    # Calculamos monto original y porcentaje de reembolso
    monto_pagado = pago.monto if pago else Decimal('0.00')
    porcentaje = reserva.vehiculo.politica_reembolso or Decimal('0.00')
    reembolso = (monto_pagado * porcentaje) / Decimal('100.00')

    if request.method == 'POST':
        reserva.estado = 'cancelada'
        reserva.save()

        if pago and pago.estado == 'exitoso' and pago.tarjeta:
            tarjeta = pago.tarjeta
            tarjeta.saldo += reembolso
            tarjeta.save()

            pago.estado = 'fallido'  
            pago.save()

        # 3) Enviar correo de confirmación de cancelación
        send_mail(
            subject='Reserva Cancelada - Alquileres María',
            message=f"""
Hola {request.user.nombre or request.user.username},

Tu reserva para el vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo} ha sido cancelada.

Detalles de la cancelación:
- Fecha de inicio: {reserva.fecha_inicio}
- Fecha de fin: {reserva.fecha_fin}
- Monto pagado originalmente: ${monto_pagado:.2f}

Según la política de reembolso del vehículo ({porcentaje:.2f}%), se te ha reintegrado:
- Monto de reembolso: ${reembolso:.2f}

El saldo reembolsado ya se acreditó a tu tarjeta terminada en {pago.tarjeta.numero_tarjeta[-4:] if pago and pago.tarjeta else '----'}.

Si tienes dudas, no dudes en contactarnos.

Atentamente,
El equipo de Alquileres María
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.correo],
            fail_silently=False,
        )

        messages.success(request, "Reserva cancelada exitosamente. Se ha aplicado el reembolso.")
        return redirect('reservas:reserva_cancelada')  # o la vista que uses tras cancelar
    else:
        # Renderizamos un template de confirmación previo a cancelar
        return render(
            request,
            'reservas/reserva_cancelar.html',
            {
                'reserva': reserva,
                'monto_pagado': monto_pagado,
                'porcentaje': porcentaje,
                'reembolso': reembolso,
            }
        )

def reserva_cancelada(request):
    return render(request, 'reservas/reserva_cancelada.html')

@login_required#creo q esto no va
def reserva_modificar(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    auto = reserva.vehiculo

    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva, auto=auto)
        if form.is_valid():
            form.save()
            # Send modification email
            send_mail(
                subject='Reserva Modificada - Alquileres María',
                message=f"""
                Hola {request.user.nombre or request.user.username},

                Tu reserva para el vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo} ha sido modificada exitosamente.

                Nuevos detalles:
                - Fecha de inicio: {reserva.fecha_inicio}
                - Fecha de fin: {reserva.fecha_fin}

                Si tienes dudas, contáctanos.

                Atentamente,
                El equipo de Alquileres María
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.correo],
                fail_silently=False,
            )
            messages.success(request, "Reserva modificada exitosamente.")
            return redirect('historial_reservas') 
    else:
        form = ReservaForm(instance=reserva, auto=auto)

    return render(request, 'reservas/reserva_modificar.html', {
        'form': form,
        'auto': auto,
        'reserva': reserva
    })


