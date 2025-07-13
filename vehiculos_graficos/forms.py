from django import forms

OPCIONES_GRAFICO = [
    ('vehiculos_mas_alquilados', 'Vehículos más alquilados'),
    ('dinero_por_vehiculo', 'Dinero recaudado por vehículo'),
    ('vehiculos_por_sucursal', 'Cantidad de vehículos alquilados por sucursal'),
    ('dinero_por_sucursal', 'Dinero recaudado por sucursal'),
    ('vehiculos_por_usuario', 'Cantidad de vehículos alquilados por usuario'),
    ('dinero_por_usuario', 'Dinero recaudado por usuario'),
]

class FiltroGraficoForm(forms.Form):
    fecha_inicio = forms.DateField(label="Fecha inicio", widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_fin = forms.DateField(label="Fecha fin", widget=forms.DateInput(attrs={'type': 'date'}))
    tipo_grafico = forms.MultipleChoiceField(
        label="Tipo de gráfico",
        choices=OPCIONES_GRAFICO,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )