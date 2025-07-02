from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel_admin, name='panel_admin'),
    path('no_autorizado/', views.no_autorizado, name='no_autorizado'),
    path('autos/', views.lista_autos, name='lista_autos'),
    path('autos/agregar/', views.agregar_auto, name='agregar_auto'),
    path('autos/eliminar/<str:patente>', views.eliminar_auto, name='eliminar_auto'),
    path('autos/detalles/<str:patente>', views.detalle_auto, name='detalle_auto_admin'),
    path('modificar-auto/<str:patente>/', views.modificar_auto, name='modificar_auto'),
    path('crear_empleado', views.crear_empleado, name='crear_empleado'),
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleados/detalles/<str:correo>', views.detalle_empleado, name='detalle_empleado')
]