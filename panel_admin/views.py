from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from vehiculos.models import Auto
from vehiculos.forms import AutoForm
from django.shortcuts import get_object_or_404


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
    auto.delete()
    return redirect('lista_autos')