
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import registrarse, login, cerrar_sesion
urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login, name='login'),
     path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]

