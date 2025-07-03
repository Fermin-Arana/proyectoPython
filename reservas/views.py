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
    
    dias = (reserva.fecha_fin - reserva.fecha_inicio).days
    monto = reserva.vehiculo.precio_por_dia * dias
    if request.method == 'POST':
        reserva.estado = 'cancelada'
        reserva.save()
        # Send cancellation email
        send_mail(
            subject='Reserva Cancelada - Alquileres María',
            message=f"""
            Hola {request.user.nombre or request.user.username},

            Tu reserva para el vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo} ha sido cancelada.
                        Detalles:
                        - Fecha de inicio: {reserva.fecha_inicio}
                        - Fecha de fin: {reserva.fecha_fin}
                        - Monto pagado: ${monto:.2f}
            Si tienes dudas, contáctanos.

            Atentamente,
            El equipo de Alquileres María
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.correo],
            fail_silently=False,
        )
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


@login_required
def crear_reserva_empleado(request, auto_id):
    # Verificar que el usuario sea empleado o admin
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        messages.error(request, "No tienes permisos para acceder a esta función.")
        return redirect('inicio')
    
    auto = get_object_or_404(Auto, id=auto_id)
    clientes = Usuario.objects.filter(groups__name='cliente', is_active=True)
    
    if request.method == 'POST':
        # Verificar si es cliente existente o nuevo
        cliente_tipo = request.POST.get('cliente_tipo')
        
        # VALIDACIONES PERSONALIZADAS PARA EMPLEADOS
        errors = {}
        
        # 1. Validaciones de Fechas (SIN mínimo de anticipación)
        fecha_inicio_str = request.POST.get('fecha_inicio')
        fecha_fin_str = request.POST.get('fecha_fin')
        
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            
            if fecha_fin <= fecha_inicio:
                errors['fecha_fin'] = "La fecha de fin debe ser posterior a la fecha de inicio."
                
        except (ValueError, TypeError):
            if not fecha_inicio_str:
                errors['fecha_inicio'] = "La fecha de inicio es obligatoria."
            if not fecha_fin_str:
                errors['fecha_fin'] = "La fecha de fin es obligatoria."
            fecha_inicio = fecha_fin = None
        
        # 4. Validaciones de Campos Obligatorios
        conductor = request.POST.get('conductor', '').strip()
        dni_conductor = request.POST.get('dni_conductor', '').strip()
        tipo_seguro = request.POST.get('tipo_seguro')
        
        if not conductor:
            errors['conductor'] = "El nombre del conductor es obligatorio."
        if not dni_conductor:
            errors['dni_conductor'] = "El DNI del conductor es obligatorio."
        if not tipo_seguro:
            errors['tipo_seguro'] = "Debe seleccionar un tipo de seguro."
        
        # Solo continuar con validaciones avanzadas si las fechas son válidas
        if fecha_inicio and fecha_fin and not errors.get('fecha_inicio') and not errors.get('fecha_fin'):
            
            # 2. Validaciones de Disponibilidad del Vehículo
            reservas_conflicto = Reserva.objects.filter(
                vehiculo=auto,
                estado__in=['pendiente', 'confirmada'],
                fecha_inicio__lt=fecha_fin,
                fecha_fin__gt=fecha_inicio
            )
            
            if reservas_conflicto.exists():
                errors['vehiculo'] = "El vehículo no está disponible en las fechas seleccionadas."
            
            # 3. Validaciones de Conductor
            if conductor:
                # Verificar que el conductor no tenga otra reserva en las mismas fechas
                reservas_conductor = Reserva.objects.filter(
                    conductor=conductor,
                    estado__in=['pendiente', 'confirmada'],
                    fecha_inicio__lt=fecha_fin,
                    fecha_fin__gt=fecha_inicio
                )
                
                if reservas_conductor.exists():
                    errors['conductor'] = "El conductor ya tiene una reserva en esas fechas."
            
            if dni_conductor:
                # Verificar que el DNI no esté en otra reserva en las mismas fechas
                reservas_dni = Reserva.objects.filter(
                    dni_conductor=dni_conductor,
                    estado__in=['pendiente', 'confirmada'],
                    fecha_inicio__lt=fecha_fin,
                    fecha_fin__gt=fecha_inicio
                )
                
                if reservas_dni.exists():
                    errors['dni_conductor'] = "Este DNI ya está asociado a otra reserva en las mismas fechas."
        
        # Si hay errores, mostrarlos y volver al formulario
        if errors:
            for field, error in errors.items():
                messages.error(request, f"{error}")
            return render(request, 'reservas/crear_reserva_empleado.html', {
                'auto': auto,
                'clientes': clientes,
                'form_data': request.POST,
                'errors': errors
            })
        
        # Procesar cliente (existente o nuevo)
        if cliente_tipo == 'existente':
            cliente_id = request.POST.get('cliente_id')
            cliente = get_object_or_404(Usuario, id=cliente_id)
        else:
            # Crear nuevo cliente (código existente)
            try:
                from usuarios.utils import generar_password_temporal, enviar_email_activacion
                password_temporal = generar_password_temporal()
                
                cliente = Usuario.objects.create_user(
                    username=request.POST.get('nuevo_username'),
                    password=password_temporal,
                    nombre=request.POST.get('nuevo_nombre'),
                    apellido=request.POST.get('nuevo_apellido'),
                    dni=request.POST.get('nuevo_dni'),
                    correo=request.POST.get('nuevo_correo'),
                    telefono=request.POST.get('nuevo_telefono'),
                    fecha_nacimiento=request.POST.get('nuevo_fecha_nacimiento'),
                    is_active=False,
                    created_by_employee=True
                )
                
                cliente.password_temp = password_temporal
                cliente.save()
                
                from django.contrib.auth.models import Group
                cliente_group, created = Group.objects.get_or_create(name='cliente')
                cliente.groups.add(cliente_group)
                
                if enviar_email_activacion(cliente, password_temporal):
                    messages.success(request, 
                        f"Cliente {cliente.nombre} {cliente.apellido} creado exitosamente. "
                        f"Se ha enviado un email de activación a {cliente.correo}.")
                else:
                    messages.warning(request, 
                        f"Cliente creado pero hubo un error enviando el email. "
                        f"Contraseña temporal: {password_temporal}")
                
            except Exception as e:
                messages.error(request, f"Error al crear el cliente: {str(e)}")
                return render(request, 'reservas/crear_reserva_empleado.html', {
                    'auto': auto,
                    'clientes': clientes,
                    'form_data': request.POST
                })
        
        # Crear reserva con todas las validaciones aplicadas
        try:
            reserva = Reserva(
                usuario=cliente,
                vehiculo=auto,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                tipo_seguro=tipo_seguro,
                conductor=conductor,
                dni_conductor=dni_conductor,
                estado='confirmada'
            )
            
            # Aplicar configuración de seguros
            reserva.seguro_basico = False
            reserva.seguro_completo = False
            reserva.seguro_premium = False
            
            if tipo_seguro == 'basico':
                reserva.seguro_basico = True
            elif tipo_seguro == 'completo':
                reserva.seguro_completo = True
            elif tipo_seguro == 'premium':
                reserva.seguro_premium = True
            
            reserva.save()
            
            if cliente_tipo == 'nuevo':
                messages.info(request, 
                    f"IMPORTANTE: El cliente debe activar su cuenta antes de poder gestionar la reserva.")
            
            messages.success(request, f"Reserva creada exitosamente para {cliente.nombre} {cliente.apellido}")
            return redirect('reserva_exitosa', reserva_id=reserva.id)
            
        except Exception as e:
            messages.error(request, f"Error al crear la reserva: {str(e)}")
    
    return render(request, 'reservas/crear_reserva_empleado.html', {
        'auto': auto,
        'clientes': clientes
    })