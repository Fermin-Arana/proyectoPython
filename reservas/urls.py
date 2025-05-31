from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('<int:auto_id>/', views.crear_reserva, name='crear_reserva'),
    path('<int:auto_id>/<int:reserva_id>/', views.crear_reserva, name='crear_reserva'),
    path('<int:reserva_id>/pagar/', views.pagar_reserva, name='pagar_reserva'),
    path('reserva_exitosa/<int:reserva_id>/', views.reserva_exitosa, name='reserva_exitosa'),
    path('reserva_cancelar/<int:reserva_id>/', views.reserva_cancelar, name='reserva_cancelar'),
    path('reserva_cancelada/', views.reserva_cancelada, name='reserva_cancelada'),
    path('reserva/<int:reserva_id>/modificar/', views.reserva_modificar, name='reserva_modificar'),
    
]
