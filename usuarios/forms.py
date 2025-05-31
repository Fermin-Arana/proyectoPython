from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from .models import Usuario
from datetime import date
import re

class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        return UserModel._default_manager.filter(correo__iexact=email, is_active=True)

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
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Ej: juan84551'}),
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Juan'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Ej: Pérez'}),
            'dni': forms.TextInput(attrs={'placeholder': 'Ej: 40505968'}),
            'correo': forms.EmailInput(attrs={'placeholder': 'Ej: juan@gmail.com'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej: 2218974555'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username').lower()
        if Usuario.objects.filter(username__iexact=username).exists():
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

        if not password1:
            return password2
            
        if password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return password2
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        if (edad < 18):
            raise forms.ValidationError("Debes ser mayor de edad para registrarte.")
        if edad > 100:
            raise forms.ValidationError("La edad ingresada debe ser una edad real")
        
        return fecha_nacimiento
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Placeholders para campos definidos manualmente
        self.fields['username'].widget.attrs['placeholder'] = 'Ej: juan84551'
        self.fields['password1'].widget.attrs['placeholder'] = 'Contraseña segura (mínimo 8 caracteres)'
        self.fields['password2'].widget.attrs['placeholder'] = 'Repetí la contraseña'

class UserEditForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'fecha_nacimiento']
        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'correo': 'Correo electrónico',
            'telefono': 'Teléfono',
            'fecha_nacimiento': 'Fecha de nacimiento',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej: juan@gmail.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 2218974555'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'fecha'}),
        }
    
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        # Verificar si el correo ya existe, pero excluir el usuario actual
        if Usuario.objects.filter(correo=correo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso.")
        return correo
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        # Verificar si el teléfono ya existe, pero excluir el usuario actual
        if Usuario.objects.filter(telefono=telefono).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este teléfono ya está en uso.")
        return telefono