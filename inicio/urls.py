from django.urls import include, path
from .views import detalle_auto, index
from django.urls import path, include
from . import views

urlpatterns = [
    path('', index, name='index'),
    path('usuarios/', include('usuarios.urls')),
    path('perfil/', views.perfil, name='perfil'),
    path('historial-reservas/', views.historial_reservas, name='historial_reservas'),
    path("detalle_auto/<int:auto_id>/", detalle_auto, name="detalle_auto"),
]
