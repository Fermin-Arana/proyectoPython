from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel_empleado, name='panel_empleado'),
    path('no_autorizado/', views.no_autorizado_empleado, name='no_autorizado_empleado'),
    
    # Gestión de reservas
    path('reservas/', views.lista_reservas_empleado, name='lista_reservas_empleado'),
    path('reservas/crear/<int:auto_id>/', views.crear_reserva_empleado, name='crear_reserva_empleado'),
    path('reservas/cambiar-estado/<int:reserva_id>/', views.cambiar_estado_reserva, name='cambiar_estado_reserva_empleado'),
    path('reservas/devolver/<int:reserva_id>/', views.devolver_auto, name='devolver_auto_empleado'),
    
    # Gestión de autos
    path('autos/', views.lista_autos_empleado, name='lista_autos_empleado'),
    path('autos/cambiar-estado/<str:patente>/', views.cambiar_estado_auto_empleado, name='cambiar_estado_auto_empleado'),
]