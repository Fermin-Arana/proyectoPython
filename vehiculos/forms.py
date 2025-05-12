from django import forms
from django.core.exceptions import ValidationError
from .models import Auto

class AutoForm(forms.ModelForm):
    class Meta:
        model = Auto
        fields = '__all__'  # O especificá campos si querés
        widgets = {
            'patente': forms.TextInput(attrs={'placeholder': 'Ej: ABC123 o AB123CD'})
        }
        
    def clean_patente(self):
        patente = self.cleaned_data['patente']
        if Auto.objects.filter(patente=patente).exists():
            raise ValidationError("Ya existe un auto con esa patente.")
        return patente