from datetime import datetime, timedelta
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

    def clean_fecha_inicio(self):
        hoy = datetime.today().date()
        pasado = hoy + timedelta(days=2)
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        if fecha_inicio < pasado:
            raise forms.ValidationError("La reserva debe tener al menos 2 días de anticipación")
        return fecha_inicio

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        vehiculo = cleaned_data.get('vehiculo')

        # Validar que fecha_fin no sea anterior a fecha_inicio
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')

        # Validar disponibilidad del vehículo
        if fecha_inicio and fecha_fin and vehiculo:
            reservas_conflicto = Reserva.objects.filter(
                vehiculo=vehiculo,
                fecha_inicio__lt=fecha_fin,
                fecha_fin__gt=fecha_inicio,
                estado='pendiente'  # Ajusta según estados que bloquean reserva
            )
            # Excluir la reserva actual en caso de edición (opcional)
            if self.instance.pk:
                reservas_conflicto = reservas_conflicto.exclude(pk=self.instance.pk)

            if reservas_conflicto.exists():
                raise ValidationError('El vehículo ya está reservado para esas fechas.')

        return cleaned_data
