from django.urls import path
from . import views

urlpatterns = [
    path('autos-mas-alquilados/', views.autos_mas_alquilados, name='autos_mas_alquilados'),
]