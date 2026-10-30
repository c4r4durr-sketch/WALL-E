"""
python manage.py cargar_fotos_demo

Asigna una ilustración generada por código (PNG 600x600, sin descargar
nada) a cada herramienta que todavía no tiene foto, para tener algo que
mostrar en el catálogo. Las herramientas con foto no se tocan; correrlo
dos veces no hace nada la segunda vez.
"""

import io
import zlib

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw

from apps.catalogo.domain.entities import ImagenProducto
from apps.catalogo.infrastructure.repositories import HerramientaRepositoryDjango
from apps.catalogo.use_cases import gestionar_herramientas as casos

LADO = 600
# Fondos neutros y tintas de la paleta (docs/DISENO.md).
FONDOS = ["#F2F2F5", "#FFEDE0", "#E8EEF7", "#EAF4EC", "#F5EFE6"]
TINTA = "#1D1D1F"
ACENTO = "#C2410C"


def _dibujar(semilla: int) -> bytes:
    """Una herramienta estilizada (mango + cabeza) sobre fondo suave; la
    semilla (sale del código) varía color, ángulo y forma de la cabeza."""
    fondo = FONDOS[semilla % len(FONDOS)]
    imagen = Image.new("RGB", (LADO, LADO), fondo)
    lienzo = ImageDraw.Draw(imagen)

    # Mango en diagonal.
    lienzo.rounded_rectangle((270, 190, 330, 500), radius=30, fill=TINTA)
    lienzo.rounded_rectangle((280, 380, 320, 490), radius=20, fill=ACENTO)
    # Cabeza: tres formas posibles (martillo, llave, destornillador).
    forma = semilla % 3
    if forma == 0:
        lienzo.rounded_rectangle((170, 120, 430, 210), radius=26, fill=TINTA)
    elif forma == 1:
        lienzo.ellipse((205, 80, 395, 270), fill=TINTA)
        lienzo.rounded_rectangle((268, 70, 332, 170), radius=14, fill=fondo)
    else:
        lienzo.polygon([(300, 70), (340, 200), (260, 200)], fill=TINTA)

    angulo = (semilla % 7) * 8 - 24
    imagen = imagen.rotate(angulo, resample=Image.Resampling.BICUBIC, fillcolor=fondo)
    salida = io.BytesIO()
    imagen.save(salida, format="PNG", optimize=True)
    return salida.getvalue()


class Command(BaseCommand):
    help = "Asigna ilustraciones generadas por código a las herramientas sin foto."

    def handle(self, *args, **opciones):
        repo = HerramientaRepositoryDjango()
        pendientes = casos.herramientas_sin_foto(repo)
        for herramienta in pendientes:
            contenido = _dibujar(zlib.crc32(herramienta.codigo.encode()))
            imagen = ImagenProducto(
                nombre=f"{herramienta.codigo}.png",
                formato="PNG",
                tamano_bytes=len(contenido),
                contenido=ContentFile(contenido),
            )
            with transaction.atomic():
                casos.asignar_foto(repo, herramienta.id, imagen)
        self.stdout.write(self.style.SUCCESS(f"Fotos de demostración asignadas: {len(pendientes)}."))
