from django.shortcuts import redirect, render
<<<<<<< HEAD
from .forms import CustomUserCreationForm
from django.contrib.auth import login as auth_login, logout, authenticate
=======
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from usuarios.models import Usuario
from .forms import CustomPasswordResetForm, CustomUserCreationForm
from django.contrib.auth import  login as auth_login, logout, authenticate, get_user_model
>>>>>>> a1f21d685f238f57e620bfeaa742cc390a630947
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
<<<<<<< HEAD
=======
from .utils import generar_codigo_otp
from decouple import config
import time
>>>>>>> a1f21d685f238f57e620bfeaa742cc390a630947

User = get_user_model()
def registrarse(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario registrado exitosamente")
            return redirect('login')  
    else:
        form = CustomUserCreationForm()

    return render(request, 'usuarios/registrar_usuario.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)

            if user is not None:
<<<<<<< HEAD
                auth_login(request, user)
                messages.success(request, "Inicio de sesión exitoso")
                return redirect("/")  # Redirige a la página principal
=======
                if user.groups.filter(name='admin').exists():
                    codigo = generar_codigo_otp()
                    request.session['codigo_2fa'] = codigo
                    request.session['user_id_2fa'] = user.id
                    request.session['codigo_2fa_timestamp'] = time.time()


                    send_mail(
                        'Código 2FA para ingresar',
                        f'Tu código es: {codigo}',
                        config('EMAIL_HOST_USER'),  # o config('EMAIL_HOST_USER')
                        [user.correo],
                        fail_silently=False,
                    )
                    return redirect('validar_codigo_2fa')
                
                else: 
                    auth_login(request, user)
                    messages.success(request, "Inicio de sesión exitoso")
                    return redirect("/")  # Redirige a la página principal
>>>>>>> a1f21d685f238f57e620bfeaa742cc390a630947
    else:
        form = AuthenticationForm()

    return render(request, "usuarios/login.html", {"form": form})

def cerrar_sesion(request):
    logout(request)
<<<<<<< HEAD
    messages.success(request, "Se cerró la sesión correctamente")  
    return redirect('/')
=======
    messages.success(request, "Se cerró la sesión correctamente") 
    return redirect('/')  # Redirige a la página principal

def recuperar_contrasena(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        try:
            usuario = Usuario.objects.get(correo=correo)
            token = default_token_generator.make_token(usuario)
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            link = f"http://{settings.DEFAULT_DOMAIN}/usuarios/password-reset-confirm/{uid}/{token}/"

            send_mail(
                subject='Restablecer tu contraseña - Alquileres María',
                message=f"""Hola {usuario.nombre or usuario.username},

Recibiste este correo porque se solicitó restablecer tu contraseña.

Hacé clic en el siguiente enlace para establecer una nueva contraseña:
{link}

Si no fuiste vos, simplemente ignorá este correo.

Gracias,
El equipo de Alquileres María
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[correo],
                fail_silently=False,
            )

            messages.success(request, "📬 Revisa tu correo para continuar con el cambio de contraseña.")
            return redirect('login')

        except Usuario.DoesNotExist:
            messages.error(request, "❌ No se encontró ningún usuario con ese correo.")
    
    return render(request, 'usuarios/recuperar_contrasena_manual.html')

>>>>>>> a1f21d685f238f57e620bfeaa742cc390a630947

class PswrdResetView(PasswordResetView):
    template_name = 'usuarios/password_reset_form.html'
    email_template_name = 'usuarios/password_reset_email.html'
    subject_template_name = 'usuarios/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
<<<<<<< HEAD
    form_class = PasswordResetForm

=======
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        print(f"📩 Se ejecutó form_valid. Enviando email a: {form.cleaned_data['email']}")
        return super().form_valid(form)
    
>>>>>>> a1f21d685f238f57e620bfeaa742cc390a630947
class PswrdResetDoneView(PasswordResetDoneView):
    template_name = 'usuarios/password_reset_done.html'

class PswrdResetConfirmView(PasswordResetConfirmView):
    template_name = 'usuarios/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    form_class = SetPasswordForm

class PswrdResetCompleteView(PasswordResetCompleteView):
    template_name = 'usuarios/password_reset_complete.html'
<<<<<<< HEAD
    
    
    
=======


def validar_codigo_2fa(request):
    if 'codigo_2fa' not in request.session or 'user_id_2fa' not in request.session:
        return redirect('no_autorizado')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')
        codigo_guardado = request.session.get('codigo_2fa')
        user_id = request.session.get('user_id_2fa')
        timestamp_guardado = request.session.get('codigo_2fa_timestamp')

        # Tiempo actual
        tiempo_actual = time.time()

        # Definimos tiempo máximo válido (en segundos)
        TIEMPO_MAXIMO = 60  # 5 minutos

        if not timestamp_guardado or (tiempo_actual - timestamp_guardado) > TIEMPO_MAXIMO:
            # Código expiró o no existe timestamp
            messages.error(request, "El código expiró. Por favor, inicia sesión de nuevo.")
            # Limpiar sesión para que intente login de nuevo
            request.session.flush()
            return redirect('login')  # o la url de login que uses

        if codigo_ingresado == codigo_guardado and user_id:
            user = User.objects.get(id=user_id)
            auth_login(request, user)  # Loguear oficialmente

            # Limpiar la sesión
            del request.session['codigo_2fa']
            del request.session['user_id_2fa']
            del request.session['codigo_2fa_timestamp']

            messages.success(request, "Autenticación 2FA exitosa")
            return redirect('panel_admin')

        else:
            messages.error(request, "Código inválido")
            return redirect('validar_codigo_2fa')

    return render(request, 'usuarios/validar_codigo.html')
>>>>>>> a1f21d685f238f57e620bfeaa742cc390a630947
