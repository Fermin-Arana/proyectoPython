from datetime import datetime, timedelta
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from usuarios.models import Usuario
from vehiculos.models import Auto
from reservas.models import Reserva, PagoSimulado, Tarjeta
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.conf import settings
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

@login_required
def panel_empleado(request):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    # Estadísticas para el dashboard
    reservas_activas = Reserva.objects.filter(estado__in=['pendiente', 'confirmada']).count()
    autos_disponibles = Auto.objects.filter(estado='disponible').count()
    autos_reservados = Auto.objects.filter(estado='reservado').count()
    
    context = {
        'reservas_activas': reservas_activas,
        'autos_disponibles': autos_disponibles,
        'autos_reservados': autos_reservados,
    }
    return render(request, 'panel_empleado/dashboard.html', context)

def no_autorizado_empleado(request):
    return render(request, 'panel_empleado/no_autorizado.html')

@login_required
def lista_reservas_empleado(request):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    # Mostrar reservas activas (pendientes y confirmadas)
    reservas_activas = Reserva.objects.filter(
        estado__in=['pendiente', 'confirmada']
    ).order_by('-fecha_reserva')
    
    return render(request, 'panel_empleado/lista_reservas.html', {
        'reservas': reservas_activas
    })

@login_required
def devolver_auto(request, reserva_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        # Finalizar la reserva
        reserva.estado = 'finalizada'
        reserva.save()
        
        # Cambiar estado del auto a disponible
        auto = reserva.vehiculo
        auto.estado = 'disponible'
        auto.save()
        
        messages.success(request, f'Vehículo {auto.patente} devuelto exitosamente. Reserva finalizada.')
        return redirect('lista_reservas_empleado')
    
    return render(request, 'panel_empleado/confirmar_devolucion.html', {'reserva': reserva})

@login_required
def cambiar_estado_reserva(request, reserva_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        estado_anterior = reserva.estado
        
        if nuevo_estado in ['pendiente', 'confirmada', 'cancelada', 'finalizada']:
            reserva.estado = nuevo_estado
            reserva.save()
            
            # Si se confirma la reserva, cambiar estado del auto
            if nuevo_estado == 'confirmada' and estado_anterior != 'confirmada':
                reserva.vehiculo.estado = 'reservado'
                reserva.vehiculo.save()
            
            # Si se cancela o finaliza, liberar el auto
            elif nuevo_estado in ['cancelada', 'finalizada'] and estado_anterior == 'confirmada':
                reserva.vehiculo.estado = 'disponible'
                reserva.vehiculo.save()
            
            messages.success(request, f'Estado de la reserva cambiado a {nuevo_estado}.')
        
        return redirect('lista_reservas_empleado')
    
    return render(request, 'panel_empleado/cambiar_estado_reserva.html', {'reserva': reserva})

@login_required
def lista_autos_empleado(request):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    autos = Auto.objects.all().order_by('estado', 'marca', 'modelo')
    return render(request, 'panel_empleado/lista_autos.html', {'autos': autos})

@login_required
def cambiar_estado_auto_empleado(request, patente):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    auto = get_object_or_404(Auto, patente=patente)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        # Los empleados solo pueden cambiar entre disponible e inhabilitado
        if nuevo_estado in ['disponible', 'inhabilitado']:
            auto.estado = nuevo_estado
            auto.save()
            messages.success(request, f'Estado del vehículo {auto.patente} cambiado a {nuevo_estado}.')
        return redirect('lista_autos_empleado')
    
    return render(request, 'panel_empleado/cambiar_estado_auto.html', {'auto': auto})


@login_required
def crear_reserva_empleado(request, auto_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
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
            return render(request, 'panel_empleado/crear_reserva_empleado.html', {
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
                return render(request, 'panel_empleado/crear_reserva_empleado.html', {
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
            return redirect('reservas:reserva_exitosa', reserva_id=reserva.id)
            
        except Exception as e:
            messages.error(request, f"Error al crear la reserva: {str(e)}")
    
    return render(request, 'panel_empleado/crear_reserva_empleado.html', {
        'auto': auto,
        'clientes': clientes
    })
