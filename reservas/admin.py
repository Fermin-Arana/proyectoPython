from django.contrib import admin
from .models import PagoSimulado, Reserva, Tarjeta

admin.site.register(Reserva)
admin.site.register(Tarjeta)