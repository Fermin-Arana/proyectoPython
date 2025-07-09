from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from reservas.models import Reserva
from django.db.models import Count
from .forms import FiltroGraficoForm

def es_admin(user):
    return user.is_authenticated and user.groups.filter(name='admin').exists()

# @user_passes_test(es_admin)
def autos_mas_alquilados(request):
    datos = None
    mensaje = None
    form = FiltroGraficoForm(request.GET or None)
    if form.is_valid():
        fecha_inicio = form.cleaned_data['fecha_inicio']
        fecha_fin = form.cleaned_data['fecha_fin']
        reservas = Reserva.objects.filter(fecha_inicio__gte=fecha_inicio, fecha_fin__lte=fecha_fin)
        if reservas.exists():
            conteo = reservas.values('vehiculo__modelo').annotate(total=Count('vehiculo')).order_by('-total')
            labels = [item['vehiculo__modelo'] for item in conteo]
            data = [item['total'] for item in conteo]
            datos = {'labels': labels, 'data': data}
        else:
            mensaje = "No hay datos disponibles"
    return render(request, "vehiculos_graficos/graficos.html", {"form": form, "datos": datos, "mensaje": mensaje})
