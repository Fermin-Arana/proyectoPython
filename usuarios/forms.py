from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
import re

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        help_text="",
        error_messages={
            'required': 'Este campo es obligatorio.',
            'max_length': 'Máximo 150 caracteres.',
        },
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="La contraseña debe tener al menos 8 caracteres y ser alfanumérica.",
        error_messages={
            'required': 'Debes ingresar una contraseña.',
        },
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="",
        error_messages={
            'required': 'Debes confirmar la contraseña.',
        },
    )

    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        error_messages={'required': 'La fecha de nacimiento es obligatoria.'},
    )

    class Meta:
        model = Usuario  
        fields = ['username', 'password1', 'password2', 'nombre', 'apellido', 'dni', 'fecha_nacimiento', 'correo', 'telefono']
        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'dni': 'DNI',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'correo': 'Correo electrónico',
            'telefono': 'Teléfono',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Ese nombre de usuario ya está en uso. Probá con otro.")
        return username

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if Usuario.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Ese DNI ya está en uso. Probá con otro.")
        return dni  

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if Usuario.objects.filter(telefono=telefono).exists():
            raise forms.ValidationError("Ese teléfono ya está en uso. Probá con otro.")
        return telefono 

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        errores = []

        if len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            errores.append("La contraseña debe ser alfanumérica (letras y números).")

        if errores:
            raise forms.ValidationError(errores)
        
        return password
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return password2
