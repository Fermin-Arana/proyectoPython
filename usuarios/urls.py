
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import registrarse, login, cerrar_sesion, PswrdResetView, PswrdResetDoneView, PswrdResetConfirmView, PswrdResetCompleteView
urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
     # Rutas para recuperación de contraseña
    path('password-reset/', PswrdResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PswrdResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PswrdResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PswrdResetCompleteView.as_view(), name='password_reset_complete'),
]

