from django.shortcuts import redirect, render
from .forms import CustomUserCreationForm
from django.contrib.auth import  login as auth_login, logout, authenticate
<<<<<<< HEAD
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
=======
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
>>>>>>> 3cf87145c39ca20c8b588af1dd49d3b491675a34

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
                auth_login(request, user)
<<<<<<< HEAD
=======
                messages.success(request, "Inicio de sesión exitoso")
>>>>>>> 3cf87145c39ca20c8b588af1dd49d3b491675a34
                return redirect("/")  # Redirige a la página principal
    else:
        form = AuthenticationForm()

    return render(request, "usuarios/login.html", {"form": form})

def cerrar_sesion(request):
    logout(request)
    messages.success(request, "Se cerró la sesión correctamente") 
<<<<<<< HEAD
    return redirect('/')  # Redirige a la página principal
=======
    return redirect('/')  # Redirige a la página principal

class PswrdResetView(PasswordResetView):
    template_name = 'usuarios/password_reset_form.html'
    email_template_name = 'usuarios/password_reset_email.html'
    subject_template_name = 'usuarios/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    form_class = PasswordResetForm

class PswrdResetDoneView(PasswordResetDoneView):
    template_name = 'usuarios/password_reset_done.html'

class PswrdResetConfirmView(PasswordResetConfirmView):
    template_name = 'usuarios/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    form_class = SetPasswordForm

class PswrdResetCompleteView(PasswordResetCompleteView):
    template_name = 'usuarios/password_reset_complete.html'
>>>>>>> 3cf87145c39ca20c8b588af1dd49d3b491675a34
