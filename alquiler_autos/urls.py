
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inicio.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('vehiculos/', include('vehiculos.urls')),
    path('reservas/', include('reservas.urls')),
    path('panel-admin/', include('panel_admin.urls')),
<<<<<<< HEAD
    path('reservar/', include('reservas.urls')),
    path('graficos/', include('vehiculos_graficos.urls')),
]
=======
    path('panel-empleado/', include('panel_empleado.urls')),  # Nueva ruta
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
>>>>>>> ramaCami

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)