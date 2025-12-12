from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from actividades.models import Actividad


class Usuario(AbstractUser):
    ROLES = (
        ('administrador', 'Administrador'),
        ('docente', 'Docente'),
        ('nino', 'Niño'),
    )
    rol = models.CharField(max_length=20, choices=ROLES)
    docente = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'rol': 'docente'},
        related_name='ninos_asignados'
    )

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class Progreso(models.Model):
    # Niño que realiza la actividad
    nino = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progresos'
    )
    # Actividad realizada
    actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        related_name='progresos'
    )

    # Para el seguimiento del docente
    completado = models.BooleanField(default=False)
    errores = models.PositiveIntegerField(default=0)

    fecha_completado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nino.username} - {self.actividad.nombre}"
