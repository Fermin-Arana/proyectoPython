from django.urls import path
from .views import registrarse, login, cerrar_sesion
from . import views

urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login, name='login'),
    path('logout/', cerrar_sesion, name='logout'),
]

