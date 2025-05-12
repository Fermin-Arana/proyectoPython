from django.urls import path
from .views import registrarse, login_view, cerrar_sesion
from . import views

urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login_view, name='login'),
    path('logout/', cerrar_sesion, name='logout'),
]

