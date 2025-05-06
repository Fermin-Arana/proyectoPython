# usuarios/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

#Esto es un formulario que Django va a usar para crear un usuario nuevo. 
#Básicamente, sirve para que alguien complete un formulario en una página web y
#Django lo guarde en la base de datos como un nuevo usuario.
class RegistrarUsuarioForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'password1', 'password2', 'nombre', 'apellido', 'dni', 'fecha_nacimiento', 'correo', 'telefono']
