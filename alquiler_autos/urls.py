
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('', include('inicio.urls')), 
    path('panel-admin/', include('panel_admin.urls')),
    path('reservar/', include('reservas.urls')),
    path('graficos/', include('vehiculos_graficos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)