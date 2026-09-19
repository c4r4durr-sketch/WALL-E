from django.db import models


class Herramienta(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=150)
    modelo = models.CharField(max_length=100, blank=True)
    unidades_por_caja = models.PositiveIntegerField(default=1)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "catalogo"
        verbose_name = "Herramienta"
        verbose_name_plural = "Herramientas"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"
