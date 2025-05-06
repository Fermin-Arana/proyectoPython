from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date
from django.core.exceptions import ValidationError
from sucursales.models import Sucursal
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class Usuario(AbstractUser):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    dni = models.CharField(max_length=10, unique=True)
    fecha_nacimiento = models.DateField()
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15)

    # Campos necesarios para evitar conflictos si vas a tener subclases como Cliente o Empleado
    groups = models.ManyToManyField(
        Group,
        related_name='usuarios',  # nombre único para evitar conflicto con el default 'user_set'
        blank=True
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='usuarios',  # idem arriba
        blank=True
    )

    def __str__(self):
        return f"{self.username} - {self.nombre} {self.apellido}"

    
class EmpleadoExtra(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    sucursal_asignada = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True)  # Aquí ya no es una cadena

