from datetime import datetime, timedelta, date
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
        return redirect('no_autorizado')
    
    context = {
        'es_admin': request.user.groups.filter(name='admin').exists(),
    }
    return render(request, 'panel_empleado/dashboard.html', context)

def no_autorizado_empleado(request):
    return render(request, 'panel_empleado/no_autorizado.html')

@login_required
def registrar_entrega_empleado(request, reserva_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')

    reserva = get_object_or_404(Reserva, id=reserva_id)
    auto = reserva.vehiculo
    
    if reserva.estado != 'confirmada':
        messages.error(request, "Solo se pueden entregar autos con reservas confirmadas.")
        return redirect('cambiar_estado_reserva_empleado', reserva_id=reserva.id)

    en_mantenimiento = auto.estado == 'mantenimiento'
    en_uso = Reserva.objects.filter(vehiculo=auto, estado='en_curso').exists()
    if en_mantenimiento or en_uso:
        reemplazo = buscar_auto_reemplazo(
            sucursal=reserva.vehiculo.sucursal,
            categoria=auto.categoria,
            precio_original=auto.precio_por_dia,
            fecha_inicio=reserva.fecha_inicio,
            fecha_fin=reserva.fecha_fin
        )

        if reemplazo:
            reserva.vehiculo = reemplazo
            reserva.estado = 'en_curso'
            reserva.save()
            notificar_reemplazo(reserva)
            messages.success(request, f"Auto original no disponible, se asignó {reemplazo.marca} {reemplazo.modelo} ({reemplazo.patente}). Cliente notificado.")
        else:
            cancelar_con_reembolso_total(reserva)
            messages.error(request, "No hay reemplazo disponible. Reserva cancelada, reembolso realizado y cliente notificado.")
    else:
        reserva.estado = 'en_curso'
        reserva.save()
        messages.success(request, "Reserva puesta en curso correctamente.")

    return redirect('lista_reservas_empleado')

from decimal import Decimal

def cancelar_con_reembolso_total(reserva):
    try:
        pago = reserva.pagosimulado
    except PagoSimulado.DoesNotExist:
        pago = None

    monto_pagado = pago.monto if pago else Decimal('0.00')
    reembolso = monto_pagado  # Reembolso del 100%

    reserva.estado = 'cancelada'
    reserva.save()

    if pago and pago.estado == 'exitoso' and pago.tarjeta:
        tarjeta = pago.tarjeta
        tarjeta.saldo += reembolso
        tarjeta.save()

        pago.estado = 'fallido'
        pago.save()

    # Enviar correo
    send_mail(
        subject='Cancelación de tu reserva y reembolso',
        message=f"""
Hola {reserva.usuario.nombre},

Tu reserva para el vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo} fue cancelada.

Monto reembolsado: ${reembolso:.2f}

Ya fue acreditado a tu tarjeta terminada en {pago.tarjeta.numero_tarjeta[-4:] if pago and pago.tarjeta else '----'}.

Lamentamos las molestias.

El equipo de Alquileres María
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reserva.usuario.correo],
        fail_silently=False,
    )

def buscar_auto_reemplazo(sucursal, categoria, precio_original, fecha_inicio, fecha_fin):
    autos_disponibles = Auto.objects.filter(
        activo=True,
        sucursal=sucursal,
        estado='disponible',
        categoria=categoria,
        precio_por_dia__gte=precio_original
    ).exclude(
        reserva__estado='en_curso'
    )

    if autos_disponibles.exists():
        return autos_disponibles.first()

    autos_alternativos = Auto.objects.filter(
        activo=True,
        sucursal=sucursal,
        estado='disponible',
        precio_por_dia__gte=precio_original
    ).exclude(
       reserva__estado='en_curso'
    )

    if autos_alternativos.exists():
        return autos_alternativos.first()

    return None

def notificar_reemplazo(reserva):
    usuario = reserva.usuario
    auto = reserva.vehiculo

    send_mail(
        'Actualización de tu reserva en Alquileres María',
        f'''Hola {usuario.nombre},

Te informamos que el vehículo originalmente asignado a tu reserva #{reserva.id} no estaba disponible al momento de la entrega.

Hemos asignado un nuevo vehículo para que puedas continuar con tu reserva sin inconvenientes.

Nuevo vehículo: {auto.marca} {auto.modelo} - Patente: {auto.patente}

Gracias por tu comprensión,
El equipo de Alquileres María''',
        settings.DEFAULT_FROM_EMAIL,
        [usuario.correo],
        fail_silently=False,
    )


@login_required
def lista_reservas_empleado(request):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')
    
    # Los administradores pueden ver todas las reservas
    if request.user.groups.filter(name='admin').exists():
        reservas = Reserva.objects.all().select_related('usuario', 'vehiculo').order_by('-fecha_reserva')
    else:
        # Los empleados solo ven reservas de su sucursal asignada
        try:
            empleado_extra = request.user.empleadoextra
            sucursal_empleado = empleado_extra.sucursal_asignada
            
            if sucursal_empleado:
                # Filtrar reservas por autos de la sucursal del empleado
                reservas = Reserva.objects.filter(
                    vehiculo__sucursal=sucursal_empleado
                ).select_related('usuario', 'vehiculo').order_by('-fecha_reserva')
            else:
                # Si el empleado no tiene sucursal asignada, no ve ninguna reserva
                reservas = Reserva.objects.none()
                messages.warning(request, 'No tienes una sucursal asignada. Contacta al administrador.')
        except:
            # Si no existe EmpleadoExtra para este usuario, no ve reservas
            reservas = Reserva.objects.none()
            messages.error(request, 'Error al obtener información del empleado. Contacta al administrador.')
    
    return render(request, 'panel_empleado/lista_reservas.html', {
        'reservas': reservas
    })

@login_required
def devolver_auto(request, reserva_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')
    
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
        return redirect('no_autorizado')
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Solo mostrar detalles, no permitir cambios
    return render(request, 'panel_empleado/cambiar_estado_reserva.html', {'reserva': reserva})

@login_required
def lista_autos_empleado(request):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')
    
    from sucursales.models import Sucursal
    from django.db.models import Q
    from datetime import datetime
    
    # Obtener todos los autos activos
    autos = Auto.objects.filter(activo=True)
    
    # Filtrar por sucursal del empleado (excepto administradores)
    if not request.user.groups.filter(name='admin').exists():
        autos = autos.exclude(estado='inhabilitado')
        try:
            empleado_extra = request.user.empleadoextra
            sucursal_empleado = empleado_extra.sucursal_asignada
            if sucursal_empleado:
                autos = autos.filter(sucursal=sucursal_empleado)
        except:
            # Si no tiene sucursal asignada, no mostrar autos
            autos = Auto.objects.none()
    
    # Filtros
    marca_filtro = request.GET.get('marca')
    estado_filtro = request.GET.get('estado')
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
                    estado__in=['pendiente', 'confirmada', 'en_curso']
                ).values_list('vehiculo_id', flat=True)
                
                if estado_filtro == 'disponible':
                    # Solo autos disponibles SIN reservas
                    autos = autos.exclude(id__in=autos_con_reserva).filter(estado='disponible')
                elif estado_filtro == 'reservado':
                    # Autos que tienen reservas activas
                    autos = autos.filter(id__in=autos_con_reserva)
                elif estado_filtro == 'mantenimiento':
                    # Solo autos en mantenimiento
                    autos = autos.filter(estado='mantenimiento')
                else:
                    autos = autos.filter(estado=estado_filtro)
            except ValueError:
                pass  # Fecha inválida, ignorar filtro de fecha
        else:
            # Sin fecha de consulta, usar fecha actual
            if estado_filtro == 'reservado':
                from django.utils import timezone
                fecha_actual = timezone.now().date()
                autos_con_reserva = Reserva.objects.filter(
                    fecha_inicio__lte=fecha_actual,
                    fecha_fin__gte=fecha_actual,
                    estado__in=['pendiente', 'confirmada', 'en_curso']
                ).values_list('vehiculo_id', flat=True)
                autos = autos.filter(id__in=autos_con_reserva)
            else:
                autos = autos.filter(estado=estado_filtro)
    
    # Filtro por sucursal removido - ahora se filtra automáticamente
    
    # Ordenar resultados
    autos = autos.order_by('estado', 'marca', 'modelo')
    
    context = {
        'autos': autos,
        'marca_actual': marca_filtro,
        'estado_actual': estado_filtro,
        'fecha_consulta': fecha_consulta,
        'es_admin': request.user.groups.filter(name='admin').exists(),
    }
    
    return render(request, 'panel_empleado/lista_autos.html', context)

@login_required
def cambiar_estado_auto_empleado(request, patente):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')
    
    auto = get_object_or_404(Auto, patente=patente)
    
    if request.method == 'POST':
        nuevo_estado = nuevo_estado = request.POST.get('estado', '').strip().lower()
        
        # Validar que no se pueda cambiar a 'mantenimiento' si hay reservas en curso
        if nuevo_estado == 'mantenimiento':
            reservas_en_curso = Reserva.objects.filter(
                vehiculo=auto,
                estado='en_curso',
            )
            if reservas_en_curso.exists():
                messages.error(request, f'No se puede cambiar a mantenimiento. El auto está siendo utilizado actualmente (reserva en curso).')
                return redirect('lista_autos_empleado')
        
        # Los empleados pueden cambiar entre disponible y mantenimiento
        # Solo los administradores pueden cambiar a inhabilitado
        estados_permitidos = ['disponible', 'mantenimiento']
        if request.user.groups.filter(name='admin').exists():
            estados_permitidos.append('inhabilitado')
        
        if nuevo_estado in estados_permitidos:
            auto.estado = nuevo_estado
            auto.save()
            messages.success(request, f'Estado del vehículo {auto.patente} cambiado a {nuevo_estado}.')
        else:
            if nuevo_estado == 'inhabilitado':
                messages.error(request, 'Solo los administradores pueden inhabilitar vehículos.')
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
        
        # Los empleados pueden cambiar entre disponible y mantenimiento
        # Solo los administradores pueden cambiar a inhabilitado
        estados_permitidos = ['disponible', 'mantenimiento']
        if request.user.groups.filter(name='admin').exists():
            estados_permitidos.append('inhabilitado')
        
        if nuevo_estado in estados_permitidos:
            # Verificar que no tenga reservas activas si se cambia a mantenimiento
            if nuevo_estado == 'mantenimiento':
                reservas_activas = Reserva.objects.filter(
                    vehiculo=auto,
                    estado__in=['pendiente', 'confirmada']
                )
                if reservas_activas.exists():
                    return JsonResponse({
                        'success': False, 
                        'error': 'No se puede cambiar a mantenimiento. El auto tiene reservas activas.'#aca habria que enviar un mensaje al usuario de la reserva para q cambie el auto
                    })
            
            auto.estado = nuevo_estado
            auto.save()
            
            # Determinar el badge HTML según el estado
            if nuevo_estado == 'disponible':
                badge_html = '<span class="badge bg-success"><i class="fas fa-check"></i> Disponible</span>'
            elif nuevo_estado == 'mantenimiento':
                badge_html = '<span class="badge bg-warning"><i class="fas fa-tools"></i> Mantenimiento</span>'
            else:  # inhabilitado
                badge_html = '<span class="badge bg-danger"><i class="fas fa-ban"></i> Inhabilitado</span>'
            
            return JsonResponse({
                'success': True, 
                'nuevo_estado': nuevo_estado,
                'badge_html': badge_html
            })
        else:
            if nuevo_estado == 'inhabilitado':
                return JsonResponse({'success': False, 'error': 'Solo los administradores pueden inhabilitar vehículos.'})
            else:
                return JsonResponse({'success': False, 'error': 'Estado no válido'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def crear_reserva_empleado(request, auto_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')
    
    auto = get_object_or_404(Auto, id=auto_id)
    
    
    if auto.estado != 'disponible':
        estado_display = {
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
        
        # Solo se permite seleccionar clientes existentes
        
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
                vehiculo=auto,
                estado__in=['pendiente', 'confirmada', 'en_curso'],
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
            
            # 4. Validaciones de Conductor Adicional
            conductor_adicional_seleccionado = 'conductor_adicional' in request.POST
            if conductor_adicional_seleccionado:
                nombre_conductor_adicional = request.POST.get('nombre_conductor_adicional', '').strip()
                dni_conductor_adicional = request.POST.get('dni_conductor_adicional', '').strip()
                
                # Validar que se ingresen los datos del conductor adicional
                if not nombre_conductor_adicional:
                    errors['nombre_conductor_adicional'] = "Debes ingresar el nombre del conductor adicional."
                if not dni_conductor_adicional:
                    errors['dni_conductor_adicional'] = "Debes ingresar el DNI del conductor adicional."
                
                # Validar que el DNI del conductor adicional no sea igual al principal
                if dni_conductor_adicional and dni_conductor and dni_conductor_adicional == dni_conductor:
                    errors['dni_conductor_adicional'] = "El DNI del conductor adicional no puede ser igual al del conductor principal."
                
                # Validar disponibilidad del conductor adicional por nombre
                if nombre_conductor_adicional:
                    reservas_conductor_adicional = Reserva.objects.filter(
                        nombre_conductor_adicional=nombre_conductor_adicional,
                        estado__in=['pendiente', 'confirmada'],
                        fecha_inicio__lt=fecha_fin,
                        fecha_fin__gt=fecha_inicio
                    )
                    if reservas_conductor_adicional.exists():
                        errors['nombre_conductor_adicional'] = "Este conductor adicional ya tiene una reserva en esas fechas."
                
                # Validar disponibilidad del DNI del conductor adicional
                if dni_conductor_adicional:
                    # Verificar como conductor adicional
                    reservas_dni_adicional = Reserva.objects.filter(
                        dni_conductor_adicional=dni_conductor_adicional,
                        estado__in=['pendiente', 'confirmada'],
                        fecha_inicio__lt=fecha_fin,
                        fecha_fin__gt=fecha_inicio
                    )
                    if reservas_dni_adicional.exists():
                        errors['dni_conductor_adicional'] = "Este DNI ya está asociado a otra reserva como conductor adicional en las mismas fechas."
                    
                    # Verificar como conductor principal
                    reservas_dni_principal = Reserva.objects.filter(
                        dni_conductor=dni_conductor_adicional,
                        estado__in=['pendiente', 'confirmada'],
                        fecha_inicio__lt=fecha_fin,
                        fecha_fin__gt=fecha_inicio
                    )
                    if reservas_dni_principal.exists():
                        errors['dni_conductor_adicional'] = "Este DNI ya está asociado a otra reserva como conductor principal en las mismas fechas."
        
        # Procesar cliente existente únicamente
        cliente = None
        cliente_id = request.POST.get('cliente_id') or request.POST.get('cliente_id_backup')
        if not cliente_id:
            errors['cliente'] = "Debe seleccionar un cliente."
        else:
            try:
                cliente = get_object_or_404(Usuario, id=cliente_id)
            except:
                errors['cliente'] = "Cliente no encontrado."
        
        # Validar que cliente exista antes de continuar
        if not cliente:
            errors['cliente'] = "Debe seleccionar un cliente."
        
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
            # Crear la reserva
            reserva = Reserva(
                usuario=cliente,
                vehiculo=auto,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                conductor=conductor,
                dni_conductor=dni_conductor,
                estado='confirmada'
            )
            
            # Configurar tipo de seguro
            reserva.tipo_seguro = tipo_seguro
            
            # Configurar seguros (mantener compatibilidad)
            reserva.seguro_basico = (tipo_seguro == 'basico')
            reserva.seguro_completo = (tipo_seguro == 'completo')
            reserva.seguro_premium = (tipo_seguro == 'premium')
            
            # Configurar adicionales
            reserva.gps = 'gps' in request.POST
            reserva.silla_bebe = 'silla_bebe' in request.POST
            reserva.conductor_adicional = 'conductor_adicional' in request.POST

            
            # Si se seleccionó conductor adicional, obtener sus datos
            if reserva.conductor_adicional:
                reserva.nombre_conductor_adicional = request.POST.get('nombre_conductor_adicional', '').strip()
                reserva.dni_conductor_adicional = request.POST.get('dni_conductor_adicional', '').strip()
            
            # En la función crear_reserva_empleado, después de reserva.save() (línea ~580)
            reserva.save()
            
            adicionales = ""
            if reserva.gps:
                adicionales += "- GPS\n"
            if reserva.silla_bebe:
                adicionales += "- Silla para bebé\n"
            if reserva.conductor_adicional:
                adicionales += f"- Conductor adicional: {reserva.nombre_conductor_adicional}\n"
            # Enviar email de confirmación de reserva
            try:
                from django.conf import settings
                send_mail(
                    subject='Reserva Confirmada - Alquileres María',
                    message=f"""
Hola {cliente.nombre} {cliente.apellido},

Tu reserva para el vehículo {auto.marca} {auto.modelo} ha sido confirmada exitosamente por nuestro personal.

Detalles de la reserva:
- Número de reserva: #{reserva.id:05d}
- Fecha de inicio: {fecha_inicio}
- Fecha de fin: {fecha_fin}
- Conductor: {conductor}
- DNI del conductor: {dni_conductor}
- Tipo de seguro: {tipo_seguro.title()}

Adicionales incluidos:
{adicionales}

¡Gracias por confiar en nosotros!

Atentamente,
El equipo de Alquileres María
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[cliente.correo],
                    fail_silently=False,
                )
                messages.success(request, f"Email de confirmación enviado a {cliente.correo}")
            except Exception as e:
                messages.warning(request, f"Reserva creada exitosamente, pero no se pudo enviar el email de confirmación: {str(e)}")
            
            # Reserva creada exitosamente
                
            messages.success(request, f"Reserva creada exitosamente para {cliente.nombre} {cliente.apellido}")
            return redirect('panel_empleado/reserva_exitosa', reserva_id=reserva.id)
            
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
        return redirect('no_autorizado')
    
    # Obtener reservas confirmadas (autos que están en uso)
    reservas_activas = Reserva.objects.filter(
        estado='en_curso'
    ).select_related('vehiculo', 'usuario').order_by('fecha_fin')
    
    return render(request, 'panel_empleado/registrar_devolucion.html', {
        'reservas_activas': reservas_activas
    })

@login_required
def procesar_devolucion_empleado(request, reserva_id):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')
    
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


@login_required
def crear_cliente_empleado(request):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')
    
    if request.method == 'POST':
        errors = {}
        
        # Obtener datos del formulario
        username = request.POST.get('username', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        dni = request.POST.get('dni', '').strip()
        correo = request.POST.get('correo', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        fecha_nacimiento = request.POST.get('fecha_nacimiento', '').strip()
        
        # Validaciones
        if not username:
            errors['username'] = "El nombre de usuario es obligatorio."
        elif Usuario.objects.filter(username=username).exists():
            errors['username'] = "Ese nombre de usuario ya está en uso. Probá con otro."
            
        if not nombre:
            errors['nombre'] = "El nombre es obligatorio."
            
        if not apellido:
            errors['apellido'] = "El apellido es obligatorio."
            
        if not dni:
            errors['dni'] = "El DNI es obligatorio."
        elif Usuario.objects.filter(dni=dni).exists():
            errors['dni'] = "Ese DNI ya está en uso. Probá con otro."
            
        if not correo:
            errors['correo'] = "El correo es obligatorio."
        elif Usuario.objects.filter(correo=correo).exists():
            errors['correo'] = "Ya existe un usuario con este Correo."
            
        if not telefono:
            errors['telefono'] = "El teléfono es obligatorio."
            
        if not fecha_nacimiento:
            errors['fecha_nacimiento'] = "La fecha de nacimiento es obligatoria."
        else:
            # Validar que sea mayor de edad
            try:
                from datetime import datetime
                fecha_nac = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                hoy = date.today()
                edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
                
                if edad < 18:
                    errors['fecha_nacimiento'] = "Debes ser mayor de edad para registrarte."
            except ValueError:
                errors['fecha_nacimiento'] = "Formato de fecha inválido."
        
        # Si no hay errores, crear el cliente
        if not errors:
            try:
                from usuarios.utils import generar_password_temporal, enviar_email_activacion
                import uuid
                
                # Generar contraseña temporal
                password_temporal = generar_password_temporal()
                
                # Crear el usuario
                cliente = Usuario.objects.create_user(
                    username=username,
                    password=password_temporal,
                    nombre=nombre,
                    apellido=apellido,
                    dni=dni,
                    correo=correo,
                    telefono=telefono,
                    fecha_nacimiento=fecha_nacimiento,
                    is_active=True,  # Activar automáticamente
                    created_by_employee=True,
                    activation_token=str(uuid.uuid4())
                )
                
                # Guardar contraseña temporal para el middleware
                cliente.password_temp = password_temporal
                cliente.save()
                
                # Asignar grupo de cliente
                from django.contrib.auth.models import Group
                cliente_group, created = Group.objects.get_or_create(name='cliente')
                cliente.groups.add(cliente_group)
                
                # Enviar email de activación
                if enviar_email_activacion(cliente, password_temporal):
                    messages.success(request, 
                        f"Cliente {cliente.nombre} {cliente.apellido} creado exitosamente. "
                        f"Se ha enviado un email con las credenciales a {cliente.correo}.")
                else:
                    messages.warning(request, 
                        f"Cliente creado pero hubo un error enviando el email. "
                        f"Contraseña temporal: {password_temporal}")
                
                return redirect('lista_autos_empleado')
                
            except Exception as e:
                messages.error(request, f"Error al crear el cliente: {str(e)}")
        else:
            # Mostrar errores
            for field, error in errors.items():
                messages.error(request, error)
    
    return render(request, 'panel_empleado/crear_cliente.html')

@login_required
def lista_clientes_empleado(request):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')
    
    # Obtener todos los clientes (usuarios que no son empleados ni admins)
    clientes = Usuario.objects.filter(
        is_active=True
    ).exclude(
        groups__name__in=['empleado', 'admin']
    ).order_by('nombre', 'apellido')
    
    return render(request, 'panel_empleado/lista_clientes.html', {
        'clientes': clientes
    })

@login_required
def detalle_auto_empleado(request, patente):
    if not (request.user.groups.filter(name='empleado').exists() or 
            request.user.groups.filter(name='admin').exists()):
        return redirect('no_autorizado')
    
    # Si el parámetro es numérico, es un ID y necesitamos redirigir a la patente correcta
    if patente.isdigit():
        try:
            auto = Auto.objects.get(id=int(patente))
            return redirect('detalle_auto_empleado', auto.patente)
        except Auto.DoesNotExist:
            pass
    
    auto = get_object_or_404(Auto, patente=patente)
    return render(request, 'panel_empleado/detalle_auto_empleado.html', {'auto': auto})
    
    