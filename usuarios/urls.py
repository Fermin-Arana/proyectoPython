from django.urls import path
from .views import registrarse, login, home_redirect

urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login, name='login'),
]