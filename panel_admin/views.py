from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from vehiculos.models import Auto
from vehiculos.forms import AutoForm, AutoEditarForm
from django.shortcuts import get_object_or_404
from django.contrib import messages
import secrets
from usuarios.forms import CrearEmpleadoForm
from django.core.mail import send_mail
from usuarios.models import Usuario
from django.conf import settings
from django.contrib.auth.models import Group


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

def crear_empleado(request):
    if request.method == 'POST':
        form = CrearEmpleadoForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            password = secrets.token_urlsafe(8)
            usuario.set_password(password)
            usuario.save()

            grupo_empleado, _ = Group.objects.get_or_create(name='empleado')
            usuario.groups.add(grupo_empleado)

            send_mail(
                'Tu cuenta en Alquileres María',
                f'Hola {usuario.nombre},\n\nTu cuenta fue creada.\nUsuario: {usuario.username}\nContraseña: {password}\n\nPor favor cambia tu contraseña luego de ingresar.',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.correo],
                fail_silently=False,
            )

            return redirect('panel_admin')
    
    else:
        form = CrearEmpleadoForm()
    
    return render(request, 'panel_admin/crear_empleado.html', {'form': form})