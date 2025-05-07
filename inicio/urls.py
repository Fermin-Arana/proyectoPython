from django.urls import include, path
from .views import detalle_auto, index #perfil


urlpatterns = [
    path('', index, name='index'),
    path('usuarios/', include('usuarios.urls')),
    #path("perfil/", perfil, name="perfil"),path("perfil/", perfil, name="perfil"),
    
    path("detalle_auto/<int:auto_id>/", detalle_auto, name="detalle_auto"),
]
