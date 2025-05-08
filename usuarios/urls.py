from django.urls import path
from .views import registrarse, login

urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login, name='login'),
]