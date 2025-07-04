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
    fecha_nacimiento = models.DateField(null=True, blank=True)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15)


    groups = models.ManyToManyField(
        Group,
        related_name='usuarios',  
        blank=True
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='usuarios', 
        blank=True
    )
    
    def save(self, *args, **kwargs):
        if self.username:
            self.username = self.username.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.nombre} {self.apellido}"
    
    

    
class EmpleadoExtra(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    sucursal_asignada = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True)
    activo = models.BooleanField(default=True)
    correo_original = models.EmailField(null=True, blank=True)

