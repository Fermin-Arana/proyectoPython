from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from datetime import date

class Sucursal(models.Model):
    nombre = models.CharField(max_length=50, unique=True)  
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def __str__(self):
        return self.nombre 