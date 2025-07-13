from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from vehiculos.models import Auto
from vehiculos.forms import AutoForm, AutoEditarForm
from django.shortcuts import get_object_or_404
from django.contrib import messages
import secrets
import string
from usuarios.forms import CrearEmpleadoForm
from django.core.mail import send_mail
from usuarios.models import EmpleadoExtra, Usuario
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.crypto import get_random_string
from django.contrib.auth.models import Group
from usuarios.models import Usuario
from usuarios.forms import CustomUserCreationForm, UserEditForm
from usuarios.utils import generar_password_temporal, enviar_email_activacion
from django.db.models import Q




@login_required
def panel_admin(request):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')  # o mostrar un mensaje
    return render(request, 'panel_admin/dashboard.html')

def no_autorizado(request):
    return render(request, 'panel_admin/no_autorizado.html')

def filtrar_por_estado(queryset, estado):
    if estado == 'activos':
        return queryset.filter(activo=True)
    elif estado == 'inactivos':
        return queryset.filter(activo=False)
    else:  
        return queryset

@login_required
def lista_autos(request):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    
    estado_actual = request.GET.get('estado', 'todo') 
    nombres_estado = {
        'activos': 'Activos',
        'inactivos': 'Eliminados',
        'todo': 'Todos'
    }
    estado_nombre = nombres_estado.get(estado_actual, 'Todos')

    busqueda = request.GET.get('busqueda', '').strip()

    autos = filtrar_por_estado(Auto.objects.all(), estado_actual)

    if busqueda:
        autos = autos.filter(
        Q(patente__icontains=busqueda) |
        Q(marca__icontains=busqueda) |
        Q(modelo__icontains=busqueda)
    )


    return render(request, 'panel_admin/lista_autos.html', {
        'autos': autos,
        'estado_actual': estado_actual,
        'estado_nombre': estado_nombre,
        'busqueda' : busqueda
    })

def lista_empleados(request):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    estado_actual = request.GET.get('estado', 'todo') 
    nombres_estado = {
        'activos': 'Activos',
        'inactivos': 'Eliminados',
        'todo': 'Todos'
    }
    estado_nombre = nombres_estado.get(estado_actual, 'Todos')

    busqueda = request.GET.get('busqueda', '').strip()

    empleados = filtrar_por_estado(EmpleadoExtra.objects.select_related('usuario', 'sucursal_asignada'), estado_actual)

    if busqueda:
        empleados = empleados.filter(
            usuario__dni__icontains=busqueda
        )

    return render(request, 'panel_admin/lista_empleados.html', {
        'empleados': empleados,
        'estado_actual': estado_actual,
        'estado_nombre': estado_nombre,
        'busqueda': busqueda
        })

def detalle_empleado(request, correo):
    empleado = get_object_or_404(EmpleadoExtra, usuario__correo=correo)
    return render(request, 'panel_admin/detalle_empleado.html', {'empleado': empleado})

def agregar_auto(request):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    
    if request.method == 'POST': 
        form = AutoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_autos')
    else: 
        form = AutoForm()

    return render(request, 'panel_admin/agregar_auto.html', {'form': form})

def eliminar_auto(request, patente):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    
    auto = get_object_or_404(Auto, patente=patente)

    reservas_activas = auto.reserva_set.filter(estado__in=['confirmada', 'en_curso'])

    if (reservas_activas.exists()):
        messages.error(request, "No se puede eliminar este auto porque tiene reservas activas")
        return redirect('lista_autos')

    if request.method == 'POST':
        auto.activo = False
        auto.save()
        messages.success(request, f"El vehículo con patente {auto.patente} fue deshabilitado con éxito.")
        return redirect('lista_autos')

    return render(request, 'panel_admin/confirmar_eliminar.html', {'auto': auto})

def detalle_auto(request, patente):
    auto = get_object_or_404(Auto, patente=patente)
    return render(request, 'panel_admin/detalle_auto.html', {'auto': auto})

def modificar_auto(request, patente):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    
    auto = get_object_or_404(Auto, patente=patente)

    if request.method == 'POST':
        form = AutoEditarForm(request.POST, request.FILES, instance=auto)
        if form.is_valid():
            form.save()
            return redirect('detalle_auto_admin', auto.patente)
    else:
        form = AutoEditarForm(instance=auto)

    return render(request, 'panel_admin/modificar_auto.html', {'form': form, 'auto': auto})

def generar_password_alfanumerica(longitud=8):
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def crear_empleado(request):
    if request.method == 'POST':
        form = CrearEmpleadoForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            password = generar_password_alfanumerica(8)
            usuario.set_password(password)
            usuario.is_active = True
            usuario.save()

            grupo_empleado, _ = Group.objects.get_or_create(name='empleado')
            usuario.groups.add(grupo_empleado)

            sucursal = form.cleaned_data['sucursal_asignada']
            EmpleadoExtra.objects.create(usuario=usuario, sucursal_asignada=sucursal)


            send_mail(
                'Tu cuenta en Alquileres María',
                f'Hola {usuario.nombre},\n\nTu cuenta fue creada.\nUsuario: {usuario.username}\nContraseña: {password}',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.correo],
                fail_silently=False,
            )
            messages.success(request, f"Empleado registrado correctamente!. Se ha enviado un correo electrónico con la contraseña.")
            return redirect('lista_empleados')
    
    else:
        form = CrearEmpleadoForm()
    
    return render(request, 'panel_admin/crear_empleado.html', {'form': form})

def eliminar_empleado(request,correo):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    
    empleado = get_object_or_404(EmpleadoExtra, usuario__correo=correo)

    if request.method == 'POST':
        if not empleado.correo_original:
            empleado.correo_original = empleado.usuario.correo

        empleado.usuario.correo = f"borrado_{get_random_string(8)}@gmail.com"
        empleado.usuario.is_active = False
        empleado.usuario.save()
        empleado.activo = False
        empleado.save()
        messages.success(request, f"El empleado '{empleado.usuario.nombre} {empleado.usuario.apellido}' fue dado de baja.")
        return redirect('lista_empleados')
    
    return render(request, 'panel_admin/confirmar_eliminar_empleado.html', {'empleado': empleado})
