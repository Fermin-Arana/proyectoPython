from django import forms
from .models import Auto

class AutoForm(forms.ModelForm):
    class Meta:
        model = Auto
        fields = '__all__'  # O especificá campos si querés
        widgets = {
            'patente': forms.TextInput(attrs={'placeholder': 'Ej: ABC123 o AB123CD'})
        }