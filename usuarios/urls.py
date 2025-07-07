from django.urls import path
from .views import recuperar_contrasena, registrarse, login_view, cerrar_sesion, PswrdResetView, PswrdResetDoneView, PswrdResetConfirmView, PswrdResetCompleteView, validar_codigo_2fa, activar_cuenta, cambiar_password_inicial

app_name = 'usuarios' 

urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login_view, name='login'),
    path('logout/', cerrar_sesion, name='logout'),
    path('recuperar-contrasena/', recuperar_contrasena, name='recuperar_contrasena_manual'),
    path('password-reset/', PswrdResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PswrdResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PswrdResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PswrdResetCompleteView.as_view(), name='password_reset_complete'),
    path('validar-codigo-2fa/', validar_codigo_2fa, name='validar_codigo_2fa'),
    path('activar/<uuid:token>/', activar_cuenta, name='activar_cuenta'),
    path('cambiar-password-inicial/', cambiar_password_inicial, name='cambiar_password_inicial'),
]

