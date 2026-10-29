"""
Ilustraciones de herramientas generadas por código para el comando
cargar_demo (PNG 600x600, sin descargar nada). Cada tipo de herramienta
tiene su propio dibujo; la semilla (la posición de la herramienta en la
lista) cambia el fondo y un poco el ángulo, para que dos del mismo tipo
no se vean idénticas.

El módulo empieza con "_" para que Django no lo tome como un comando.
"""

import io
import math

from PIL import Image, ImageDraw

from .cargar_fotos_demo import ACENTO, FONDOS, LADO, TINTA

METAL = "#8E8E93"
METAL_CLARO = "#C7C7CC"
AMARILLO = "#F2C94C"
VERDE_BURBUJA = "#B7E4C7"
ROJO_LASER = "#E5484D"


def _martillo(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.rounded_rectangle((278, 200, 322, 520), radius=20, fill=TINTA)
    d.rounded_rectangle((272, 390, 328, 520), radius=24, fill=ACENTO)
    d.rounded_rectangle((170, 130, 400, 210), radius=18, fill=METAL)
    d.polygon([(400, 140), (470, 110), (440, 170), (400, 200)], fill=METAL)


def _taladro(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.rounded_rectangle((150, 180, 440, 290), radius=40, fill=ACENTO)
    d.polygon([(300, 280), (380, 280), (360, 470), (290, 470)], fill=TINTA)
    d.rounded_rectangle((250, 460, 420, 530), radius=16, fill=TINTA)
    d.rectangle((110, 210, 152, 260), fill=METAL)
    d.rectangle((40, 228, 112, 242), fill=METAL_CLARO)
    d.ellipse((330, 205, 370, 245), fill=TINTA)


def _llave(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.rounded_rectangle((282, 170, 318, 450), radius=16, fill=METAL)
    # Boca abierta arriba, anillo abajo.
    d.ellipse((230, 90, 370, 230), fill=METAL)
    d.polygon([(275, 80), (325, 80), (315, 160), (285, 160)], fill=fondo)
    d.ellipse((240, 400, 360, 520), fill=METAL)
    d.ellipse((275, 435, 325, 485), fill=fondo)
    d.rounded_rectangle((290, 260, 310, 360), radius=8, fill=ACENTO)


def _alicate(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.polygon([(280, 260), (310, 270), (240, 520), (200, 510)], fill=ACENTO)
    d.polygon([(320, 260), (290, 270), (360, 520), (400, 510)], fill=ACENTO)
    d.polygon([(255, 270), (345, 270), (320, 90), (280, 90)], fill=METAL)
    d.line((300, 100, 300, 260), fill=fondo, width=6)
    d.ellipse((282, 252, 318, 288), fill=TINTA)


def _sierra(d: ImageDraw.ImageDraw, fondo: str) -> None:
    # Arco: marco en C con la hoja dentada abajo.
    d.line((120, 200, 120, 380), fill=TINTA, width=22)
    d.line((120, 200, 480, 200), fill=TINTA, width=22)
    d.line((480, 200, 480, 380), fill=TINTA, width=22)
    d.rectangle((120, 372, 480, 392), fill=METAL)
    for x in range(124, 480, 18):
        d.polygon([(x, 392), (x + 9, 408), (x + 18, 392)], fill=METAL)
    d.rounded_rectangle((90, 360, 150, 500), radius=24, fill=ACENTO)


def _serrucho(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.polygon([(110, 250), (430, 210), (430, 330), (110, 300)], fill=METAL)
    for x in range(110, 430, 16):
        y = 300 + (x - 110) * 30 / 320
        d.polygon([(x, y), (x + 8, y + 14), (x + 16, y + 1)], fill=METAL)
    d.rounded_rectangle((420, 190, 530, 360), radius=34, fill=ACENTO)
    d.rounded_rectangle((450, 230, 505, 320), radius=20, fill=fondo)


def _nivel(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.rounded_rectangle((70, 255, 530, 345), radius=14, fill=ACENTO)
    for x in (110, 265, 420):
        d.rounded_rectangle((x, 280, x + 70, 320), radius=14, fill=VERDE_BURBUJA)
        d.ellipse((x + 25, 288, x + 45, 312), fill="#FFFFFF")
    d.rectangle((70, 340, 530, 345), fill=TINTA)


def _nivel_laser(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.line((300, 60, 300, 560), fill=ROJO_LASER, width=6)
    d.line((40, 300, 560, 300), fill=ROJO_LASER, width=6)
    d.rounded_rectangle((210, 230, 390, 420), radius=24, fill=ACENTO)
    d.rounded_rectangle((240, 250, 360, 330), radius=14, fill=TINTA)
    d.ellipse((280, 270, 320, 310), fill=ROJO_LASER)
    d.rectangle((280, 420, 320, 470), fill=TINTA)
    d.rounded_rectangle((220, 465, 380, 495), radius=10, fill=TINTA)


def _cinta(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.rectangle((400, 380, 560, 420), fill=AMARILLO)
    for x in range(410, 560, 15):
        d.line((x, 380, x, 395 if (x // 15) % 2 else 402), fill=TINTA, width=3)
    d.rounded_rectangle((150, 170, 430, 450), radius=60, fill=ACENTO)
    d.ellipse((230, 250, 350, 370), fill=TINTA)
    d.ellipse((270, 290, 310, 330), fill=METAL_CLARO)
    d.rounded_rectangle((180, 440, 260, 470), radius=8, fill=TINTA)


def _sierra_circular(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.ellipse((90, 170, 370, 450), fill=METAL)
    for i in range(24):
        a = math.radians(i * 15)
        x, y = 230 + 140 * math.cos(a), 310 + 140 * math.sin(a)
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=METAL)
    d.ellipse((215, 295, 245, 325), fill=TINTA)
    d.pieslice((70, 150, 390, 470), start=200, end=340, fill=TINTA)
    d.rounded_rectangle((250, 200, 500, 330), radius=50, fill=ACENTO)
    d.rounded_rectangle((420, 150, 520, 230), radius=30, fill=TINTA)


def _destornillador(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.rectangle((290, 110, 310, 330), fill=METAL)
    d.polygon([(290, 110), (310, 110), (304, 80), (296, 80)], fill=METAL)
    d.rounded_rectangle((262, 320, 338, 530), radius=34, fill=ACENTO)
    for x in (280, 300, 320):
        d.line((x, 350, x, 500), fill=TINTA, width=5)


def _amoladora(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.ellipse((330, 140, 530, 340), fill=METAL)
    d.ellipse((415, 225, 445, 255), fill=TINTA)
    d.pieslice((320, 130, 540, 350), start=180, end=360, fill=TINTA)
    d.rounded_rectangle((90, 260, 430, 340), radius=38, fill=TINTA)
    d.rounded_rectangle((120, 270, 260, 330), radius=26, fill=ACENTO)
    d.rounded_rectangle((350, 330, 380, 460), radius=12, fill=TINTA)


def _disco(d: ImageDraw.ImageDraw, fondo: str) -> None:
    d.ellipse((110, 110, 490, 490), fill=METAL)
    d.ellipse((170, 170, 430, 430), fill=METAL_CLARO)
    d.ellipse((210, 210, 390, 390), fill=ACENTO)
    d.ellipse((265, 265, 335, 335), fill=fondo)


DIBUJOS = {
    "martillo": _martillo,
    "taladro": _taladro,
    "llave": _llave,
    "alicate": _alicate,
    "sierra": _sierra,
    "sierra_circular": _sierra_circular,
    "serrucho": _serrucho,
    "nivel": _nivel,
    "nivel_laser": _nivel_laser,
    "cinta": _cinta,
    "destornillador": _destornillador,
    "amoladora": _amoladora,
    "disco": _disco,
}


def dibujar(tipo: str, semilla: int) -> bytes:
    """PNG de una herramienta del tipo pedido sobre un fondo suave."""
    fondo = FONDOS[semilla % len(FONDOS)]
    imagen = Image.new("RGB", (LADO, LADO), fondo)
    DIBUJOS[tipo](ImageDraw.Draw(imagen), fondo)
    angulo = ((semilla // len(FONDOS)) % 5) * 4 - 8
    imagen = imagen.rotate(angulo, resample=Image.Resampling.BICUBIC, fillcolor=fondo)
    salida = io.BytesIO()
    imagen.save(salida, format="PNG", optimize=True)
    return salida.getvalue()
