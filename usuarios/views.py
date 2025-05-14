from django.shortcuts import redirect, render
from .forms import CustomUserCreationForm
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

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


def login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth_login(request, user)
                messages.success(request, "Inicio de sesión exitoso")
                return redirect("/")  # Redirige a la página principal
    else:
        form = AuthenticationForm()

    return render(request, "usuarios/login.html", {"form": form})

def cerrar_sesion(request):
    logout(request)
    messages.success(request, "Se cerró la sesión correctamente")  
    return redirect('/') 