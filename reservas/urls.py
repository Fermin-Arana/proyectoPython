from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('crear/<int:auto_id>/', views.crear_reserva, name='crear_reserva'),
    path('pagar/<int:reserva_id>/', views.pagar_reserva, name='pagar_reserva'),
    path('exitosa/', views.reserva_exitosa, name='reserva_exitosa'),
    path('cancelar/<int:reserva_id>/', views.reserva_cancelar, name='reserva_cancelar'),
    path('cancelada/', views.reserva_cancelada, name='reserva_cancelada'),
    path('modificar/<int:reserva_id>/', views.reserva_modificar, name='reserva_modificar'),
]