from django.urls import path
<<<<<<< HEAD
from .views import registrarse, login_view, cerrar_sesion
from . import views
=======
from .views import registrarse, login_view, cerrar_sesion, PswrdResetView, PswrdResetDoneView, PswrdResetConfirmView, PswrdResetCompleteView
>>>>>>> 3cf87145c39ca20c8b588af1dd49d3b491675a34

urlpatterns = [
    path('registrarse/', registrarse, name='registrarse'),
    path('login/', login_view, name='login'),
    path('logout/', cerrar_sesion, name='logout'),
<<<<<<< HEAD
=======
    path('password-reset/', PswrdResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PswrdResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PswrdResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PswrdResetCompleteView.as_view(), name='password_reset_complete'),
>>>>>>> 3cf87145c39ca20c8b588af1dd49d3b491675a34
]

