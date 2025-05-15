from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('reservar/', views.crear_reserva, name='crear_reserva'),
    path('reserva_exitosa/', views.reserva_exitosa, name='reserva_exitosa'),
    path('<int:auto_id>/', views.crear_reserva, name='crear_reserva'),
]
