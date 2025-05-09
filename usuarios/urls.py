from django.urls import path
from .views import registrarse, login
from . import views

urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login, name='login'),
]