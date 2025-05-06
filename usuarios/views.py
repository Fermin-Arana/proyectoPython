from django.shortcuts import render, redirect
from .forms import RegistrarUsuarioForm

def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistrarUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Podés cambiar esto por la página que quieras mostrar luego de registrarse
    else:
        form = RegistrarUsuarioForm()

    return render(request, 'usuarios/registrar_usuario.html', {'form': form})
