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
from datetime import datetime
import pytz
from django.http import JsonResponse
from django.db.models import Q

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
    
    # Solo mostrar detalles, no permitir cambios
    return render(request, 'panel_empleado/cambiar_estado_reserva.html', {'reserva': reserva})

@login_required
def lista_autos_empleado(request):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    from sucursales.models import Sucursal
    from django.db.models import Q
    from datetime import datetime
    
    # Obtener todos los autos activos
    autos = Auto.objects.filter(activo=True)
    
    # Filtros
    marca_filtro = request.GET.get('marca')
    estado_filtro = request.GET.get('estado')
    sucursal_filtro = request.GET.get('sucursal')
    fecha_consulta = request.GET.get('fecha_consulta')
    
    # Aplicar filtros
    if marca_filtro:
        autos = autos.filter(marca__icontains=marca_filtro)
    
    if estado_filtro:
        if fecha_consulta:
            # Si hay fecha de consulta, verificar el estado del auto en esa fecha
            try:
                fecha_obj = datetime.strptime(fecha_consulta, '%Y-%m-%d').date()
                # Verificar si el auto tenía reservas en esa fecha
                autos_con_reserva = Reserva.objects.filter(
                    fecha_inicio__lte=fecha_obj,
                    fecha_fin__gte=fecha_obj,
                    estado__in=['pendiente', 'confirmada']
                ).values_list('vehiculo_id', flat=True)
                
                if estado_filtro == 'disponible':
                    autos = autos.exclude(id__in=autos_con_reserva).filter(
                        Q(estado='disponible') | Q(estado='mantenimiento')
                    )
                elif estado_filtro == 'reservado':
                    autos = autos.filter(id__in=autos_con_reserva)
                else:
                    autos = autos.filter(estado=estado_filtro)
            except ValueError:
                pass  # Fecha inválida, ignorar filtro de fecha
        else:
            autos = autos.filter(estado=estado_filtro)
    
    if sucursal_filtro:
        autos = autos.filter(sucursal_id=sucursal_filtro)
    
    # Ordenar resultados
    autos = autos.order_by('estado', 'marca', 'modelo')
    
    # Obtener sucursales para el filtro
    sucursales = Sucursal.objects.all().order_by('nombre')
    
    # Estadísticas
    if fecha_consulta:
        try:
            fecha_obj = datetime.strptime(fecha_consulta, '%Y-%m-%d').date()
            autos_con_reserva = Reserva.objects.filter(
                fecha_inicio__lte=fecha_obj,
                fecha_fin__gte=fecha_obj,
                estado__in=['pendiente', 'confirmada']
            ).values_list('vehiculo_id', flat=True)
            
            total_disponibles = autos.exclude(id__in=autos_con_reserva).filter(
                Q(estado='disponible') | Q(estado='mantenimiento')
            ).count()
            total_reservados = autos.filter(id__in=autos_con_reserva).count()
        except ValueError:
            total_disponibles = autos.filter(estado='disponible').count()
            total_reservados = autos.filter(estado='reservado').count()
    else:
        total_disponibles = autos.filter(estado='disponible').count()
        total_reservados = autos.filter(estado='reservado').count()
    
    total_mantenimiento = autos.filter(estado='mantenimiento').count()
    total_autos = autos.count()
    
    context = {
        'autos': autos,
        'sucursales': sucursales,
        'total_disponibles': total_disponibles,
        'total_reservados': total_reservados,
        'total_mantenimiento': total_mantenimiento,
        'total_autos': total_autos,
        'marca_actual': marca_filtro,
        'estado_actual': estado_filtro,
        'sucursal_actual': sucursal_filtro,
        'fecha_consulta': fecha_consulta,
    }
    
    return render(request, 'panel_empleado/lista_autos.html', context)

@login_required
def cambiar_estado_auto_empleado(request, patente):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    auto = get_object_or_404(Auto, patente=patente)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        
        # ✅ MEJORAR: Validar que no se pueda cambiar a 'reservado' si hay reservas activas
        if nuevo_estado == 'disponible':
            # Verificar que no tenga reservas activas
            reservas_activas = Reserva.objects.filter(
                vehiculo=auto,
                estado__in=['pendiente', 'confirmada']
            )
            if reservas_activas.exists():
                messages.error(request, f'No se puede cambiar a disponible. El auto tiene reservas activas.')
                return redirect('lista_autos_empleado')
        
        # Los empleados pueden cambiar entre disponible, inhabilitado y mantenimiento
        if nuevo_estado in ['disponible', 'inhabilitado', 'mantenimiento']:
            auto.estado = nuevo_estado
            auto.save()
            messages.success(request, f'Estado del vehículo {auto.patente} cambiado a {nuevo_estado}.')
        else:
            messages.error(request, 'Estado no válido.')
            
        return redirect('lista_autos_empleado')
    
    return render(request, 'panel_empleado/cambiar_estado_auto.html', {'auto': auto})


@login_required
def cambiar_estado_rapido(request, auto_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return JsonResponse({'success': False, 'error': 'No autorizado'})
    
    if request.method == 'POST':
        auto = get_object_or_404(Auto, id=auto_id)
        nuevo_estado = request.POST.get('estado')
        
        # Solo permitir cambio entre disponible y mantenimiento
        if nuevo_estado in ['disponible', 'mantenimiento']:
            # Verificar que no tenga reservas activas si se cambia a mantenimiento
            if nuevo_estado == 'mantenimiento':
                reservas_activas = Reserva.objects.filter(
                    vehiculo=auto,
                    estado__in=['pendiente', 'confirmada']
                )
                if reservas_activas.exists():
                    return JsonResponse({
                        'success': False, 
                        'error': 'No se puede cambiar a mantenimiento. El auto tiene reservas activas.'
                    })
            
            auto.estado = nuevo_estado
            auto.save()
            
            # Determinar el badge HTML según el estado
            if nuevo_estado == 'disponible':
                badge_html = '<span class="badge bg-success"><i class="fas fa-check"></i> Disponible</span>'
            else:
                badge_html = '<span class="badge bg-warning"><i class="fas fa-tools"></i> Mantenimiento</span>'
            
            return JsonResponse({
                'success': True, 
                'nuevo_estado': nuevo_estado,
                'badge_html': badge_html
            })
        else:
            return JsonResponse({'success': False, 'error': 'Estado no válido'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def crear_reserva_empleado(request, auto_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    auto = get_object_or_404(Auto, id=auto_id)
    
    
    if auto.estado != 'disponible':
        estado_display = {
            'reservado': 'reservado',
            'mantenimiento': 'en mantenimiento', 
            'inhabilitado': 'inhabilitado'
        }.get(auto.estado, auto.estado)
        
        messages.error(request, f'El auto {auto.marca} {auto.modelo} no está disponible para reservas. Estado actual: {estado_display}')
        return redirect('lista_autos_empleado')
    
    argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    fecha_hoy = timezone.now().astimezone(argentina_tz).date()
    
    
    clientes = Usuario.objects.filter(groups__name='cliente', is_active=True)
    
    # Por esta (mostrar todos los usuarios activos que no sean empleados/admins):
   
    clientes = Usuario.objects.filter(
        is_active=True
    ).exclude(
        groups__name__in=['empleado', 'admin']
    )
    print(f"Clientes encontrados: {clientes.count()}")  # Para debug
    
    if request.method == 'POST':
        errors = {}
        
        # Forzar fecha de inicio a hoy
        request.POST = request.POST.copy()
        request.POST['fecha_inicio'] = fecha_hoy.strftime('%Y-%m-%d')
        
        cliente_tipo = request.POST.get('cliente_tipo')
        
        # VALIDACIONES PERSONALIZADAS PARA EMPLEADOS
        errors = {}
        
        # 1. Validaciones de Fechas
        try:
            fecha_inicio = datetime.strptime(request.POST.get('fecha_inicio'), '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(request.POST.get('fecha_fin'), '%Y-%m-%d').date()
            
            # Validar que fecha de inicio sea hoy
            if fecha_inicio != fecha_hoy:
                errors['fecha_inicio'] = 'La fecha de inicio debe ser hoy.'
            
            # Validar que fecha fin sea posterior a fecha inicio
            if fecha_fin <= fecha_inicio:
                errors['fecha_fin'] = 'La fecha de fin debe ser posterior a la fecha de inicio.'
                
            # Verificar disponibilidad del auto en las fechas seleccionadas
            reservas_conflicto = Reserva.objects.filter(
                vehiculo=auto,  # ✅ CAMBIAR 'auto=auto' por 'vehiculo=auto'
                estado__in=['pendiente', 'confirmada'],
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio
            )
            
            if reservas_conflicto.exists():
                errors['fecha_conflicto'] = f'El auto no está disponible en las fechas seleccionadas. Ya tiene reservas confirmadas.'
                
        except ValueError:
            errors['fechas'] = 'Formato de fecha inválido.'
            
            # Corregir: usar request.POST.get en lugar de variables no definidas
            if not request.POST.get('fecha_inicio'):
                errors['fecha_inicio'] = "La fecha de inicio es obligatoria."
            if not request.POST.get('fecha_fin'):
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
            
            # ✅ VALIDACIÓN ADICIONAL: Verificar nuevamente el estado del auto antes de crear la reserva
            auto.refresh_from_db()  # Refrescar desde la base de datos
            if auto.estado != 'disponible':
                errors['vehiculo'] = f"El auto ya no está disponible. Estado actual: {auto.get_estado_display()}"
            
            # 2. Validaciones de Disponibilidad del Vehículo
            reservas_conflicto = Reserva.objects.filter(
                vehiculo=auto,  # ✅ CAMBIAR 'auto=auto' por 'vehiculo=auto'
                estado__in=['pendiente', 'confirmada'],
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio
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
        
        # Procesar cliente (existente o nuevo)
        cliente = None  # ✅ INICIALIZAR VARIABLE CLIENTE
        if cliente_tipo == 'existente':
            # Priorizar cliente seleccionado por búsqueda
            cliente_id = request.POST.get('cliente_id') or request.POST.get('cliente_id_backup')
            if not cliente_id:
                errors['cliente'] = "Debe seleccionar un cliente."
            else:
                try:
                    cliente = get_object_or_404(Usuario, id=cliente_id)
                except:
                    errors['cliente'] = "Cliente no encontrado."
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
        
        # ✅ VALIDAR QUE CLIENTE EXISTA ANTES DE CONTINUAR
        if not cliente:
            errors['cliente'] = "Debe seleccionar un cliente o crear uno nuevo."
        
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
            
            # Guardar la reserva
            reserva.save()
            
            # ✅ CAMBIAR ESTADO DEL AUTO A 'RESERVADO' (esta línea ya existe pero puede no ejecutarse por errores anteriores)
            auto.estado = 'reservado'
            auto.save()
            
            if cliente_tipo == 'nuevo':
                messages.info(request, 
                    f"IMPORTANTE: El cliente debe activar su cuenta antes de poder gestionar la reserva.")
                
            messages.success(request, f"Reserva creada exitosamente para {cliente.nombre} {cliente.apellido}")
            return redirect('reservas:reserva_exitosa', reserva_id=reserva.id)
            
        except Exception as e:
            messages.error(request, f"Error al crear la reserva: {str(e)}")
            return render(request, 'panel_empleado/crear_reserva_empleado.html', {
                'auto': auto,
                'clientes': clientes,
                'form_data': request.POST
            })
    
    context = {
        'auto': auto,
        'clientes': clientes,
        'fecha_hoy': fecha_hoy,  # Pasar fecha de hoy al template
    }
    return render(request, 'panel_empleado/crear_reserva_empleado.html', context)


@login_required
def registrar_devolucion_empleado(request):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    # Obtener reservas confirmadas (autos que están en uso)
    reservas_activas = Reserva.objects.filter(
        estado='confirmada'
    ).select_related('vehiculo', 'usuario').order_by('fecha_fin')
    
    return render(request, 'panel_empleado/registrar_devolucion.html', {
        'reservas_activas': reservas_activas
    })

@login_required
def procesar_devolucion_empleado(request, reserva_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado_empleado')
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Calcular si es devolución tardía
    from django.utils import timezone
    fecha_actual = timezone.now()
    dias_retraso, multa_retraso = reserva.calcular_multa_retraso(fecha_actual)
    es_tardia = dias_retraso > 0
    precio_total_con_multa = reserva.precio_total() + multa_retraso
    
    if request.method == 'POST':
        # Obtener el estado del auto después de la devolución
        estado_auto = request.POST.get('estado_auto', 'disponible')
        observaciones = request.POST.get('observaciones', '').strip()
        
        # Obtener datos de devolución tardía del formulario
        es_devolucion_tardia = request.POST.get('es_devolucion_tardia') == 'true'
        dias_retraso_form = int(request.POST.get('dias_retraso', 0))
        multa_retraso_form = float(request.POST.get('multa_retraso', 0))
        
        # ✅ VALIDAR: Solo permitir estados válidos para devolución
        if estado_auto not in ['disponible', 'mantenimiento']:
            messages.error(request, 'Estado de auto no válido para devolución.')
            return render(request, 'panel_empleado/confirmar_devolucion.html', {
                'reserva': reserva,
                'es_tardia': es_tardia,
                'dias_retraso': dias_retraso,
                'multa_retraso': multa_retraso,
                'precio_total_con_multa': precio_total_con_multa,
                'fecha_actual': fecha_actual
            })
        
        # Actualizar campos de la reserva
        reserva.estado = 'finalizada'
        reserva.fecha_devolucion_real = fecha_actual
        
        # Si es devolución tardía, actualizar campos correspondientes
        if es_devolucion_tardia:
            reserva.es_devolucion_tardia = True
            reserva.dias_retraso = dias_retraso_form
            reserva.multa_por_retraso = multa_retraso_form
        
        reserva.save()
        
        # Actualizar el estado del auto según la selección del empleado
        auto = reserva.vehiculo
        auto.estado = estado_auto
        auto.save()
        
        # Mensajes de confirmación
        estado_mensaje = 'disponible' if estado_auto == 'disponible' else 'en mantenimiento'
        
        if es_devolucion_tardia:
            messages.warning(request, 
                f'Devolución tardía procesada. Vehículo {auto.patente} marcado como {estado_mensaje}. '
                f'Multa aplicada: ${multa_retraso_form:.2f} por {dias_retraso_form} día(s) de retraso.')
        else:
            messages.success(request, 
                f'Devolución procesada exitosamente. '
                f'Vehículo {auto.patente} marcado como {estado_mensaje}.')
        
        if observaciones:
            messages.info(request, f'Observaciones registradas: {observaciones}')
        
        return redirect('registrar_devolucion_empleado')
    
    return render(request, 'panel_empleado/confirmar_devolucion.html', {
        'reserva': reserva,
        'es_tardia': es_tardia,
        'dias_retraso': dias_retraso,
        'multa_retraso': multa_retraso,
        'precio_total_con_multa': precio_total_con_multa,
        'fecha_actual': fecha_actual
    })


@login_required
def buscar_clientes_ajax(request):
    """Vista AJAX para buscar clientes por DNI, username o email"""
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'clientes': []})
    
    # Buscar clientes activos por DNI, username o email
    clientes = Usuario.objects.filter(
        groups__name='cliente',
        is_active=True
    ).filter(
        Q(dni__icontains=query) |
        Q(username__icontains=query) |
        Q(correo__icontains=query)
    ).distinct()[:10]  # Limitar a 10 resultados
    
    clientes_data = []
    for cliente in clientes:
        clientes_data.append({
            'id': cliente.id,
            'username': cliente.username,
            'nombre': cliente.nombre,
            'apellido': cliente.apellido,
            'dni': cliente.dni,
            'correo': cliente.correo,
            'display': f"{cliente.username} - {cliente.nombre} {cliente.apellido} (DNI: {cliente.dni}) - {cliente.correo}"
        })
    
    return JsonResponse({'clientes': clientes_data})
    
    