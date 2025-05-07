from django.urls import path
from .views import registrarse, home_redirect

urlpatterns = [
    path('', home_redirect),
    path('registrarse/', registrarse, name='registrarse'),
]