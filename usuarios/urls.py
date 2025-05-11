from django.urls import path
from .views import registrarse, login_view
from . import views

urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login_view, name='login'),
]