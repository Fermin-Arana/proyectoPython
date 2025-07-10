from django import forms
from django.core.exceptions import ValidationError
from .models import Auto

class AutoForm(forms.ModelForm):
    class Meta:
        model = Auto
        exclude = ['activo', 'estado']
        widgets = {
            'patente': forms.TextInput(attrs={'placeholder': 'Ej: ABC123 o AB123CD'})
        }
        
    def clean_patente(self):
        patente = self.cleaned_data['patente']
        if Auto.objects.filter(patente=patente).exists():
            raise ValidationError("Ya existe un auto con esa patente.")
        return patente
    
class AutoEditarForm(forms.ModelForm):
    class Meta:
        model = Auto
        exclude = ['patente', 'sucursal', 'marca', 'modelo', 'activo', 'estado', 'anio_fabricacion', 'categoria', 'capacidad_pasajeros'] 