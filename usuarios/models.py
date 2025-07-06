from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date
from django.core.exceptions import ValidationError
from sucursales.models import Sucursal
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import uuid

class Usuario(AbstractUser):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    dni = models.CharField(max_length=10, unique=True, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    correo = models.EmailField(unique=True, null=True, blank=True)  # Add null=True, blank=True
    telefono = models.CharField(max_length=15, null=True, blank=True)
    
    # Nuevos campos para activación
    is_active = models.BooleanField(default=False)  # Cuenta inactiva por defecto
    activation_token = models.UUIDField(default=uuid.uuid4, editable=False)
    password_temp = models.CharField(max_length=128, blank=True, null=True)  # Contraseña temporal
    created_by_employee = models.BooleanField(default=False)  # Creado por empleado

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
<<<<<<< HEAD
    activo = models.BooleanField(default=True)
    correo_original = models.EmailField(null=True, blank=True)
=======
>>>>>>> ramaCami

