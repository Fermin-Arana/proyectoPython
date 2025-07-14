from datetime import timedelta
from django.utils import timezone
from django import forms
from django.core.exceptions import ValidationError
from .models import Reserva
from vehiculos.models import Auto
from django.core.validators import RegexValidator

class ReservaForm(forms.ModelForm):
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        input_formats=['%Y-%m-%d'], 
        label="Fecha de inicio",
        error_messages={
            'required': 'Debes seleccionar una fecha de inicio.',
        }
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        input_formats=['%Y-%m-%d'],  
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
    dni_conductor = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="DNI del conductor",
        error_messages={
            'required': 'Debes ingresar el DNI del conductor.',
        }
    )
    
    # Campos para conductor adicional
    nombre_conductor_adicional = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Nombre del conductor adicional"
    )
    dni_conductor_adicional = forms.CharField(
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="DNI del conductor adicional"
    )
    
    # Nuevos campos para seguros
    SEGURO_CHOICES = [
        ('basico', 'Seguro Básico (Incluido)'),
        ('completo', 'Seguro Completo (+$500/día)'),
        ('premium', 'Seguro Premium (+$1000/día)')
    ]
    
    tipo_seguro = forms.ChoiceField(
        choices=SEGURO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Tipo de Seguro",
        initial='basico'
    )
    
    # Campos para servicios adicionales
    gps = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="GPS Navegador (+$200/día)"
    )
    silla_bebe = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Silla de bebé (+$150/día)"
    )
    conductor_adicional = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Conductor adicional (+$300/día)"
    )

    class Meta:
        model = Reserva
        fields = ['vehiculo', 'fecha_inicio', 'fecha_fin', 'conductor', 'dni_conductor', 'tipo_seguro',
                 'gps', 'silla_bebe', 'conductor_adicional', 
                 'nombre_conductor_adicional', 'dni_conductor_adicional']
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
        else:
            self.fields['vehiculo'].queryset = Auto.objects.all()

    def save(self, commit=True):
        reserva = super().save(commit=False)
        tipo_seguro = self.cleaned_data.get('tipo_seguro')
        
        # Resetear seguros
        reserva.seguro_basico = False
        reserva.seguro_completo = False
        reserva.seguro_premium = False
        
        # Asignar seguro seleccionado
        if tipo_seguro == 'basico':
            reserva.seguro_basico = True
        elif tipo_seguro == 'completo':
            reserva.seguro_completo = True
        elif tipo_seguro == 'premium':
            reserva.seguro_premium = True
        
        # Asignar servicios adicionales
        reserva.gps = self.cleaned_data.get('gps', False)
        reserva.silla_bebe = self.cleaned_data.get('silla_bebe', False)
        reserva.conductor_adicional = self.cleaned_data.get('conductor_adicional', False)
        reserva.nombre_conductor_adicional = self.cleaned_data.get('nombre_conductor_adicional', '')
        reserva.dni_conductor_adicional = self.cleaned_data.get('dni_conductor_adicional', '')
            
        if commit:
            reserva.save()
        return reserva

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        vehiculo = cleaned_data.get('vehiculo')
        conductor = cleaned_data.get('conductor')
        dni_conductor = cleaned_data.get('dni_conductor')
        conductor_adicional = cleaned_data.get('conductor_adicional')
        nombre_conductor_adicional = cleaned_data.get('nombre_conductor_adicional')
        dni_conductor_adicional = cleaned_data.get('dni_conductor_adicional')
        
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
                    
            # Validación para el nombre del conductor
            if (conductor and not self.errors.get('fecha_inicio') and not self.errors.get('fecha_fin')):
                hay_otro2 = Reserva.objects.filter(
                    conductor=conductor,
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
                ).exclude(pk=self.instance.pk).exists()
                if hay_otro2:
                    self.add_error('conductor', "El conductor ya tiene una reserva en esas fechas.")
                
            # Validación para el DNI del conductor
            if (dni_conductor and not self.errors.get('fecha_inicio') and not self.errors.get('fecha_fin')):
                hay_otro_dni = Reserva.objects.filter(
                    dni_conductor=dni_conductor,
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
                ).exclude(pk=self.instance.pk).exists()
                if hay_otro_dni:
                    self.add_error('dni_conductor', "Este DNI ya está asociado a otra reserva en las mismas fechas.")
        
        # Validaciones para conductor adicional
        if conductor_adicional:
            if not nombre_conductor_adicional or nombre_conductor_adicional.strip() == '':
                self.add_error('nombre_conductor_adicional', "Debes ingresar el nombre del conductor adicional.")
            if not dni_conductor_adicional or dni_conductor_adicional.strip() == '':
                self.add_error('dni_conductor_adicional', "Debes ingresar el DNI del conductor adicional.")
            
            # Validar que el DNI del conductor adicional no sea igual al principal
            if dni_conductor_adicional and dni_conductor and dni_conductor_adicional == dni_conductor:
                self.add_error('dni_conductor_adicional', "El DNI del conductor adicional no puede ser igual al del conductor principal.")
            
            # Validar disponibilidad del conductor adicional
            if (nombre_conductor_adicional and fecha_inicio and fecha_fin and not self.errors.get('fecha_inicio') and not self.errors.get('fecha_fin')):
                hay_otro_conductor_adicional = Reserva.objects.filter(
                    nombre_conductor_adicional=nombre_conductor_adicional,
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
                ).exclude(pk=self.instance.pk).exists()
                if hay_otro_conductor_adicional:
                    self.add_error('nombre_conductor_adicional', "Este conductor adicional ya tiene una reserva en esas fechas.")
            
            # Validar disponibilidad del DNI del conductor adicional
            if (dni_conductor_adicional and fecha_inicio and fecha_fin and not self.errors.get('fecha_inicio') and not self.errors.get('fecha_fin')):
                hay_otro_dni_adicional = Reserva.objects.filter(
                    dni_conductor_adicional=dni_conductor_adicional,
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
                ).exclude(pk=self.instance.pk).exists()
                if hay_otro_dni_adicional:
                    self.add_error('dni_conductor_adicional', "Este DNI ya está asociado a otra reserva como conductor adicional en las mismas fechas.")
                
                # También verificar que no esté como conductor principal
                hay_como_principal = Reserva.objects.filter(
                    dni_conductor=dni_conductor_adicional,
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
                ).exclude(pk=self.instance.pk).exists()
                if hay_como_principal:
                    self.add_error('dni_conductor_adicional', "Este DNI ya está asociado a otra reserva como conductor principal en las mismas fechas.")
                
        return cleaned_data

class PagoSimuladoForm(forms.Form):
    nombre_en_tarjeta = forms.CharField(max_length=100, label="Nombre en la tarjeta")
    numero_tarjeta = forms.CharField(
        max_length=16,
        min_length=16,
        label="Número de tarjeta",
        validators=[RegexValidator(r'^\d{16}$', message="El número debe tener 16 dígitos.")]
    )
    vencimiento = forms.CharField(
        max_length=5,
        label="Fecha de vencimiento (MM/AA)",
        validators=[RegexValidator(r'^(0[1-9]|1[0-2])\/\d{2}$', message="Formato MM/AA.")]
    )
    codigo_seguridad = forms.CharField(
        max_length=4,
        min_length=3,
        label="Código de seguridad (CVV)",
        validators=[RegexValidator(r'^\d{3,4}$', message="Código de seguridad inválido.")]
    )
    monto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Monto a pagar",
        widget=forms.NumberInput(attrs={'readonly': 'readonly'})
    )
