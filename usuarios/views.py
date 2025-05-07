from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def registrarse(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('registrarse')  
    else:
        form = CustomUserCreationForm()

    return render(request, 'usuarios/registrar_usuario.html', {'form': form})


def home_redirect(request):
    return redirect('registrarse')
