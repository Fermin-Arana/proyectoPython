from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel_admin, name='panel_admin'),
    path('no_autorizado/', views.no_autorizado, name='no_autorizado'),
    path('autos/', views.lista_autos, name='lista_autos'),
    path('autos/agregar/', views.agregar_auto, name='agregar_auto'),
    path('autos/eliminar/<str:patente>', views.eliminar_auto, name='eliminar_auto')
]