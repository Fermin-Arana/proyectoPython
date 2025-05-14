from django.db import models

from django.contrib.auth.models import User
from vehiculos.models import Auto

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Auto, on_delete=models.CASCADE)
    conductor = models.CharField(max_length=100, default='')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, default='pendiente')   

    def __str__(self):
        return f"Reserva de {self.usuario.username} para {self.vehiculo} desde {self.fecha_inicio} hasta {self.fecha_fin}"