from datetime import datetime, timedelta
from django import forms
from .models import Reserva
from vehiculos.models import Auto

class ReservaForm(forms.ModelForm):
    vehiculo = forms.ModelChoiceField(  
        queryset=Auto.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Vehículo",
        error_messages={
            'required': 'Debes seleccionar un vehículo.',
        }
    )
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha de inicio",
        error_messages={
            'required': 'Debes seleccionar una fecha de inicio.',
        }
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha de fin",
        error_messages={
            'required': 'Debes seleccionar una fecha de fin.',
        }
    )
    conductor = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Nombre del conductor",
        error_messages={
            'required': 'Debes ingresar el nombre del conductor.',
        }
    )

    class Meta:
        model = Reserva
        fields = ['vehiculo', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_fecha_inicio(self):
        hoy = datetime.today().date()
        pasado = hoy + timedelta(days=2)
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        if fecha_inicio < pasado:
            raise forms.ValidationError("La reserva debe tener al menos 2 dias de anticipacion")
        return fecha_inicio

