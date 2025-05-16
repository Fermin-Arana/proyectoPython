from datetime import datetime, timedelta, timezone
from django import forms
from django.core.exceptions import ValidationError
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
        fields = ['vehiculo', 'fecha_inicio', 'fecha_fin', 'conductor']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        auto = kwargs.pop('auto', None)
        super().__init__(*args, **kwargs)
        if auto:
            self.fields['vehiculo'].initial = auto
            self.fields['vehiculo'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        vehiculo = cleaned_data.get('vehiculo')
        conductor = cleaned_data.get('conductor')
        
        if fecha_inicio is None:
            self.add_error('fecha_inicio', "La fecha de inicio es obligatoria.")
        if fecha_fin is None:
            self.add_error('fecha_fin', "La fecha de fin es obligatoria.")
            
        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                self.add_error('fecha_fin', "La fecha de fin debe ser posterior a la fecha de inicio.")

            hoy = timezone.now().date()
            minimo_fecha = hoy + timedelta(days=2)
            if fecha_inicio < minimo_fecha:
                self.add_error('fecha_inicio', "La reserva debe tener al menos 2 días de anticipación.")
                
            if (vehiculo and not self.errors.get('fecha_inicio') and not self.errors.get('fecha_fin')):
                hay_otro = Reserva.objects.filter(
                    vehiculo=vehiculo,
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
                ).exclude(pk=self.instance.pk).exists()
                if hay_otro:
                    self.add_error('vehiculo', "El vehículo ya está reservado en esas fechas.")
                    
            if (conductor and not self.errors.get('fecha_inicio') and not self.errors.get('fecha_fin')):
                hay_otro2 = Reserva.objects.filter(
                    conductor=conductor,
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
                ).exclude(pk=self.instance.pk).exists()
                if hay_otro2:
                    self.add_error('conductor', "El conductor ya tiene una reserva en esas fechas.")
                
        return cleaned_data
