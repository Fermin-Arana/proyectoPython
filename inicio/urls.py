from django.urls import include, path
from .views import detalle_auto, index, perfil, historial_reservas, detalle_reserva, detalle_auto
from django.urls import path, include
from . import views


urlpatterns = [
    path('', index, name='index'),
    path('usuarios/', include('usuarios.urls')),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('historial-reservas/', views.historial_reservas, name='historial_reservas'),
    path("detalle_auto/<int:auto_id>/", detalle_auto, name="detalle_auto"),
    path('detalle-reserva/<int:reserva_id>/', views.detalle_reserva, name='detalle_reserva'),
]
