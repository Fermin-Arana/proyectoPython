from django.urls import path
from . import views

urlpatterns = [
    path('registrarse/', views.registrar_usuario, name='registrarse'),
]
