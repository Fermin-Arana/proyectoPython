from django.db import models

from django.conf import settings

from vehiculos.models import Auto

class Reserva(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Auto, on_delete=models.CASCADE)
    conductor = models.CharField(max_length=100, default='')
    dni_conductor = models.CharField(max_length=20, default='')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, default='pendiente')   

    def __str__(self):
        return f"Reserva de {self.usuario.username} para {self.vehiculo} desde {self.fecha_inicio} hasta {self.fecha_fin}"
    
    
class PagoSimulado(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    nombre_en_tarjeta = models.CharField(max_length=100)
    numero_tarjeta = models.CharField(max_length=16)
    vencimiento = models.CharField(max_length=5)  # MM/AA
    codigo_seguridad = models.CharField(max_length=4)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        choices=[("exitoso", "Exitoso"), ("fallido", "Fallido")],
        default="pendiente"
    )
    fecha_pago = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.id} - {self.estado}"