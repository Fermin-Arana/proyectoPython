from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from vehiculos.models import Auto
from vehiculos.forms import AutoForm, AutoEditarForm
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import Group
from usuarios.models import Usuario
from usuarios.forms import CustomUserCreationForm, UserEditForm
from usuarios.utils import generar_password_temporal, enviar_email_activacion



@login_required
def panel_admin(request):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')  # o mostrar un mensaje
    return render(request, 'panel_admin/dashboard.html')

def no_autorizado(request):
    return render(request, 'panel_admin/no_autorizado.html')

@login_required
def lista_autos(request):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    autos = Auto.objects.all()
    return render(request, 'panel_admin/lista_autos.html',{'autos': autos})

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

    if request.method == 'POST':
        auto.delete()
        messages.success(request, f"El vehículo con patente {auto.patente} fue eliminado con éxito.")
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

@login_required
def lista_empleados(request):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    
    empleados = Usuario.objects.filter(groups__name='empleado', is_active=True)
    return render(request, 'panel_admin/lista_empleados.html', {'empleados': empleados})

@login_required
def crear_empleado(request):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            # Crear el empleado
            empleado = form.save(commit=False)
            
            # Generar contraseña temporal
            password_temporal = generar_password_temporal()
            empleado.set_password(password_temporal)
            empleado.created_by_employee = True  # Forzar cambio de contraseña
            empleado.save()
            
            # Agregar al grupo empleado
            grupo_empleado, created = Group.objects.get_or_create(name='empleado')
            empleado.groups.add(grupo_empleado)
            
            # Enviar email con contraseña temporal
            enviar_email_activacion(empleado.email, empleado.username, password_temporal)
            
            messages.success(request, f'Empleado {empleado.username} creado exitosamente. Se envió email con contraseña temporal.')
            return redirect('lista_empleados')
    else:
        form = UsuarioForm()
    
    return render(request, 'panel_admin/crear_empleado.html', {'form': form})

@login_required
def eliminar_empleado(request, empleado_id):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    
    empleado = get_object_or_404(Usuario, id=empleado_id, groups__name='empleado')
    
    if request.method == 'POST':
        empleado.is_active = False
        empleado.save()
        messages.success(request, f'Empleado {empleado.username} desactivado exitosamente.')
        return redirect('lista_empleados')
    
    return render(request, 'panel_admin/confirmar_eliminar_empleado.html', {'empleado': empleado})

@login_required
def cambiar_estado_auto(request, patente):
    if not request.user.groups.filter(name='admin').exists():
        return redirect('no_autorizado')
    
    auto = get_object_or_404(Auto, patente=patente)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in ['disponible', 'reservado', 'inhabilitado', 'mantenimiento']:
            auto.estado = nuevo_estado
            auto.save()
            messages.success(request, f'Estado del vehículo {auto.patente} cambiado a {nuevo_estado}.')
        return redirect('lista_autos')
    
    return render(request, 'panel_admin/cambiar_estado_auto.html', {'auto': auto})