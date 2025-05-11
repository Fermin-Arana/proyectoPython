from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from datetime import date
from sucursales.models import Sucursal
from django.core.validators import RegexValidator

CATEGORIAS = [
    ('E', 'Económico'),
    ('C', 'Compacto'),
    ('S', 'Sedán'),
    ('V', 'SUV'),
    ('P', 'Pickup'),
]

class Auto(models.Model):
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio_fabricacion = models.PositiveIntegerField()
    km = models.PositiveIntegerField()
    patente = models.CharField(max_length=20, unique=True,validators=[
        RegexValidator(
            regex=r'^([A-Z]{3}\d{3}|[a-z]{3}\d{3}|[a-z]{2}\d{3}[a-z]{2}|[A-Z]{2}\d{3}[A-Z]{2})$',
            message='Ingrese una patente válida (formato ABC123 o AB123CD)',
        )
    ])
    categoria = models.CharField(max_length=1, choices=CATEGORIAS)
    capacidad_pasajeros = models.PositiveIntegerField()
    politica_reembolso = models.DecimalField(max_digits=4, decimal_places=2, default=20.00)
    precio_por_dia = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='autos/', null=True, blank=True)

    def _str_(self):
        return f"{self.marca} {self.modelo} ({self.patente})"
    
