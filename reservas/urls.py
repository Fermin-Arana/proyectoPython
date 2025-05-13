from django.urls import path
from . import views

urlpatterns = [
    path('reservar/', views.crear_reserva, name='crear_reserva'),
]
