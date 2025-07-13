from django import forms
from .models import Sucursal
from usuarios.models import Usuario 

class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = ['nombre', 'direccion', 'telefono']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if Sucursal.objects.filter(nombre=nombre).exists():
            raise forms.ValidationError("Ya existe una sucursal con ese nombre.")
        return nombre

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')

        if telefono:
            # Validar que no esté en otra sucursal
            if Sucursal.objects.filter(telefono=telefono).exists():
                raise forms.ValidationError("Ya existe una sucursal con este teléfono.")

            # Validar que no esté en ningún usuario
            if Usuario.objects.filter(telefono=telefono).exists():
                raise forms.ValidationError("Este teléfono ya está registrado por un usuario del sistema.")
        
        return telefono
