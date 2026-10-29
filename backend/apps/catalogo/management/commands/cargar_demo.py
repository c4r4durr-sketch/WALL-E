"""
python manage.py cargar_demo [--reiniciar]

Carga datos de ejemplo de inventario para probar y para la demo: 4
proveedores, 20 herramientas de ferretería (con foto generada por código y
todos los datos de EOQ/ROP) y 12 meses de entradas, salidas y
transferencias en las sucursales activas que existan. Al final pone en
promoción una herramienta estancada.

  - Sin --reiniciar no hace nada si ya hay herramientas cargadas.
  - Con --reiniciar primero borra el inventario: herramientas y sus fotos,
    movimientos, transferencias, promociones, historial de costos y
    proveedores. Nunca toca usuarios, sucursales ni la auditoría.

Todo pasa por los casos de uso (registrar_herramienta, registrar_salida,
completar_transferencia, crear_promocion...), así que se cumplen las mismas
reglas que en la API: no hay salidas sin stock ni promociones sobre
herramientas que no estén estancadas. Los casos de uso fechan todo "ahora";
para tener historia, después de cada operación se le pone su fecha real en
el pasado (único acceso directo al ORM, junto con el borrado).

La historia se arma con un generador con semilla fija: correrlo dos veces
da los mismos datos. Está pensada para que se vean resultados:
  - CIN-8M, ALI-PUN6, NIV-24 y TAL-13 dejan de reponerse los últimos 75
    días y terminan bajo su punto de reorden (alertas del panel);
  - LLA-TUBO, NIV-LAS y SIE-CIR se vendieron por última vez hace 55, 75 y
    150 días en la primera sucursal (12 días antes en cada una de las
    otras), y ATO-12V ingresó hace 100 días y nunca se vendió (estancadas);
  - las ventas van de 1500 discos al año a casi nada, para que la
    clasificación ABC tenga herramientas A, B y C;
  - SIE-CIR queda con una promoción del 25 % en la primera sucursal.
"""

import math
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.catalogo.domain.entities import ImagenProducto
from apps.catalogo.infrastructure.models import Herramienta as HerramientaModel
from apps.catalogo.infrastructure.models import HistorialCosto as HistorialCostoModel
from apps.catalogo.infrastructure.models import Promocion as PromocionModel
from apps.catalogo.infrastructure.repositories import (
    HerramientaRepositoryDjango,
    HistorialCostoRepositoryDjango,
    PromocionRepositoryDjango,
)
from apps.catalogo.use_cases import gestionar_herramientas
from apps.indicadores.domain.formulas import DIAS_POR_ANIO
from apps.indicadores.use_cases.promociones import crear_promocion
from apps.movimientos.domain.value_objects import TipoUnidad
from apps.movimientos.infrastructure.models import Movimiento as MovimientoModel
from apps.movimientos.infrastructure.repositories import MovimientoRepositoryDjango
from apps.movimientos.use_cases.registrar_movimiento import registrar_entrada, registrar_salida
from apps.proveedores.infrastructure.models import Proveedor as ProveedorModel
from apps.proveedores.infrastructure.repositories import ProveedorRepositoryDjango
from apps.proveedores.use_cases.gestionar_proveedores import registrar_proveedor
from apps.transferencias.infrastructure.models import Transferencia as TransferenciaModel
from apps.transferencias.infrastructure.repositories import TransferenciaRepositoryDjango
from apps.transferencias.use_cases import gestionar_transferencias
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.value_objects import Rol
from apps.usuarios.infrastructure.repositories import SucursalRepositoryDjango, UsuarioRepositoryDjango

from ._dibujos_demo import dibujar

SEMILLA = 2026
DIAS_DE_HISTORIA = 360
# Las herramientas "reorden" no se reponen en este último tramo.
DIAS_SIN_REPONER = 75
# Días con ventas en un año (sin domingos): de acá sale la probabilidad de
# que haya una venta en un día cualquiera.
DIAS_DE_VENTA_AL_ANIO = 313

PROVEEDORES = [
    {"nombre": "Ferretería Industrial Andina", "telefono": "+591 2 2456789", "email": "ventas@andina.example"},
    {"nombre": "Distribuidora El Constructor", "telefono": "+591 3 3345678", "email": "pedidos@elconstructor.example"},
    {"nombre": "Herramientas del Sur", "telefono": "+591 4 4223344", "email": "contacto@herramientasdelsur.example"},
    {"nombre": "Importadora Tecnopower", "telefono": "+591 71234567", "email": "importaciones@tecnopower.example"},
]


@dataclass(frozen=True)
class HerramientaDemo:
    codigo: str
    nombre: str
    modelo: str
    dibujo: str
    unidades_por_caja: int
    costo: str  # Bs por unidad
    proveedor: int  # índice en PROVEEDORES
    costo_pedido: str  # S, Bs por pedido
    costo_almacenamiento: str  # H, Bs por unidad al año
    tiempo_entrega_dias: int
    demanda_anual: int  # D, unidades al año entre todas las sucursales
    por_venta: int  # unidades que se llevan en una venta típica
    perfil: str = "normal"  # normal | reorden | estancada | sin_venta
    dias_sin_venta: int = 0  # estancada: cuándo fue la última venta
    costo_anterior: Optional[str] = None  # si cambió de precio hace 120 días


HERRAMIENTAS = [
    HerramientaDemo("DIS-CORTE", 'Disco de corte para metal 4 1/2"', "115 x 1,0 mm", "disco", 50, "6.50", 3, "120", "1.30", 10, 1500, 20),
    HerramientaDemo("CIN-5M", "Cinta métrica 5 m", "Carcasa ABS con freno", "cinta", 24, "22.00", 1, "90", "4.40", 10, 420, 4, costo_anterior="19.50"),
    HerramientaDemo("DES-SET", "Juego de destornilladores 6 piezas", "Phillips y planos, punta imantada", "destornillador", 12, "42.00", 1, "90", "8.40", 12, 300, 3),
    HerramientaDemo("ALI-UNI8", 'Alicate universal 8"', "Mango aislado 1000 V", "alicate", 12, "38.00", 2, "100", "7.60", 14, 260, 3),
    HerramientaDemo("MAR-16", "Martillo de carpintero 16 oz", "Uña curva, mango de fibra", "martillo", 12, "45.00", 2, "100", "9.00", 14, 220, 3, costo_anterior="40.00"),
    HerramientaDemo("LLA-AJU10", 'Llave ajustable 10"', "Cromo vanadio", "llave", 12, "58.00", 0, "110", "11.60", 15, 150, 2),
    HerramientaDemo("CIN-8M", "Cinta métrica 8 m", "Cinta de 25 mm, imán en la punta", "cinta", 24, "35.00", 1, "90", "7.00", 25, 140, 2, "reorden"),
    HerramientaDemo("ALI-PUN6", 'Alicate de punta 6"', "Punta larga, mango aislado", "alicate", 12, "34.00", 2, "100", "6.80", 21, 120, 2, "reorden"),
    HerramientaDemo("SIE-ARCO", 'Arco de sierra 12"', "Marco tubular, hoja bimetálica", "sierra", 10, "48.00", 0, "110", "9.60", 12, 110, 2),
    HerramientaDemo("NIV-24", 'Nivel de aluminio 24"', "3 burbujas, base magnética", "nivel", 10, "55.00", 0, "110", "11.00", 30, 90, 2, "reorden"),
    HerramientaDemo("SER-CAR", 'Serrucho de carpintero 20"', "Dientes templados", "serrucho", 10, "62.00", 2, "100", "12.40", 15, 70, 1),
    HerramientaDemo("MAR-GOMA", "Mazo de goma 450 g", "Cabeza negra, mango de madera", "martillo", 12, "32.50", 2, "100", "6.50", 15, 60, 1),
    HerramientaDemo("TAL-13", "Taladro percutor 13 mm 750 W", "Velocidad variable, reversible", "taladro", 4, "420.00", 3, "150", "84.00", 30, 60, 1, "reorden", costo_anterior="395.00"),
    HerramientaDemo("ALI-PRE", 'Alicate de presión 10"', "Mordaza curva", "alicate", 10, "52.00", 2, "100", "10.40", 14, 50, 1),
    HerramientaDemo("AMO-115", 'Amoladora angular 4 1/2" 850 W', "Interruptor lateral, empuñadura auxiliar", "amoladora", 4, "310.00", 3, "150", "62.00", 20, 45, 1),
    HerramientaDemo("LLA-COMB", "Juego de llaves combinadas 8 a 22 mm", "12 piezas, estuche de lona", "llave", 6, "185.00", 0, "110", "37.00", 20, 36, 1),
    HerramientaDemo("LLA-TUBO", 'Llave para tubo 14"', "Tipo Stillson, hierro fundido", "llave", 6, "95.00", 0, "110", "19.00", 20, 24, 1, "estancada", 55),
    HerramientaDemo("NIV-LAS", "Nivel láser de líneas cruzadas", "Alcance 15 m, autonivelante", "nivel_laser", 4, "380.00", 3, "150", "76.00", 25, 14, 1, "estancada", 75),
    HerramientaDemo("SIE-CIR", 'Sierra circular 7 1/4" 1400 W', "Disco de 24 dientes incluido", "sierra_circular", 2, "690.00", 3, "150", "138.00", 25, 10, 1, "estancada", 150),
    HerramientaDemo("ATO-12V", "Atornillador inalámbrico 12 V", "2 baterías, cargador rápido", "taladro", 4, "520.00", 3, "150", "104.00", 25, 12, 1, "sin_venta", 100),
]

# Promoción vigente al terminar (sobre una estancada, en la primera sucursal).
PROMOCION = {"codigo": "SIE-CIR", "descuento_porcentaje": 25, "dias": 30,
             "motivo": "Sin ventas hace 5 meses: liquidar el stock."}
# Transferencias que no mueven stock: una pendiente y una rechazada.
TRANSFERENCIA_PENDIENTE = ("DES-SET", 2)  # (código, hace cuántos días)
TRANSFERENCIA_RECHAZADA = ("LLA-AJU10", 20)
MOTIVO_RECHAZO = "La sucursal de destino ya repuso con el proveedor."


@dataclass(frozen=True)
class Evento:
    """Una operación planificada: `cantidad` va en cajas para las
    entradas y en unidades para lo demás."""

    dia: int  # hace cuántos días
    minuto: int  # minuto del día (hora local)
    secuencia: int
    tipo: str  # entrada | salida | transferencia | pendiente | rechazada
    codigo: str
    sucursal: int  # índice en la lista de sucursales activas
    cantidad: int
    destino: Optional[int] = None


def planificar(herramienta: HerramientaDemo, n_sucursales: int, rng: random.Random) -> list[Evento]:
    """Simula un año de una herramienta en todas las sucursales y devuelve
    las operaciones en orden. Lleva su propio stock: nunca planifica una
    salida o una transferencia que el caso de uso fuera a rechazar."""
    eventos: list[Evento] = []

    def agregar(dia, minuto, tipo, sucursal, cantidad, destino=None):
        eventos.append(Evento(dia, minuto, len(eventos), tipo, herramienta.codigo, sucursal, cantidad, destino))

    caja = herramienta.unidades_por_caja
    if herramienta.perfil == "sin_venta":
        agregar(herramienta.dias_sin_venta, 9 * 60, "entrada", 0, 2)
        return eventos

    # La primera sucursal vende un 50 % más que cada una de las otras.
    pesos = [1.5] + [1.0] * (n_sucursales - 1)
    anual = [herramienta.demanda_anual * p / sum(pesos) for p in pesos]
    s, h = float(herramienta.costo_pedido), float(herramienta.costo_almacenamiento)
    # Se repone cuando la venta dejaría el stock por debajo del consumo del
    # tiempo de entrega más dos semanas; el pedido es el EOQ en cajas.
    minimo = [max(2, math.ceil(a * (herramienta.tiempo_entrega_dias + 15) / DIAS_POR_ANIO)) for a in anual]
    lote = [max(1, math.ceil(max(math.sqrt(2 * a * s / h), m) / caja)) for a, m in zip(anual, minimo)]

    stock = [0] * n_sucursales
    for i in range(n_sucursales):
        cajas = lote[i] + math.ceil(minimo[i] / caja)
        agregar(DIAS_DE_HISTORIA, 8 * 60 + i, "entrada", i, cajas)
        stock[i] += cajas * caja

    for dia in range(DIAS_DE_HISTORIA - 1, -1, -1):
        if n_sucursales > 1 and stock[0] >= 3:
            for codigo, hace, tipo in ((*TRANSFERENCIA_PENDIENTE, "pendiente"), (*TRANSFERENCIA_RECHAZADA, "rechazada")):
                if codigo == herramienta.codigo and dia == hace:
                    agregar(dia, 10 * 60, tipo, 0, 3, destino=1)
        for i in range(n_sucursales):
            # Estancada: la última venta es justo ese día (12 días antes en
            # cada sucursal siguiente) y después no se vende más.
            ultima_venta = herramienta.dias_sin_venta + 12 * i
            if herramienta.perfil == "estancada" and dia < ultima_venta:
                continue
            forzada = herramienta.perfil == "estancada" and dia == ultima_venta
            if not forzada and rng.random() >= anual[i] / (DIAS_DE_VENTA_AL_ANIO * herramienta.por_venta):
                continue
            minuto = rng.randint(9 * 60, 19 * 60)
            vendidas = rng.randint(1, 2 * herramienta.por_venta - 1)
            repone = not (herramienta.perfil == "reorden" and dia < DIAS_SIN_REPONER)
            if repone and stock[i] - vendidas < minimo[i]:
                # A veces la sucursal pide a la primera lo justo para seguir
                # vendiendo, en vez de hacerle un pedido al proveedor.
                pedido = minimo[i] + vendidas - stock[i] + math.ceil(minimo[i] / 2)
                if i > 0 and stock[0] - pedido >= minimo[0] and rng.random() < 0.4:
                    agregar(dia, minuto - 30, "transferencia", 0, pedido, destino=i)
                    stock[0] -= pedido
                    stock[i] += pedido
                else:
                    agregar(dia, minuto - 30, "entrada", i, lote[i])
                    stock[i] += lote[i] * caja
            elif not repone:
                vendidas = min(vendidas, stock[i] - 1)  # sin reposición: no se agota del todo
            if vendidas > 0:
                agregar(dia, minuto, "salida", i, vendidas)
                stock[i] -= vendidas

    if herramienta.perfil == "reorden":
        # Ventas grandes de ayer para dejar el stock total en la mitad del
        # punto de reorden, por si la simulación no bajó lo suficiente.
        objetivo = int(herramienta.demanda_anual * herramienta.tiempo_entrega_dias / DIAS_POR_ANIO / 2)
        sobrante = sum(stock) - objetivo
        for i in sorted(range(n_sucursales), key=lambda j: -stock[j]):
            quitar = min(sobrante, stock[i])
            if quitar > 0:
                agregar(1, 17 * 60 + i, "salida", i, quitar)
                stock[i] -= quitar
                sobrante -= quitar
    return eventos


class Command(BaseCommand):
    help = "Carga proveedores, herramientas y 12 meses de movimientos de ejemplo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reiniciar",
            action="store_true",
            help="Borra antes el inventario (no usuarios, sucursales ni auditoría).",
        )

    def handle(self, *args, reiniciar=False, **opciones):
        self.herramientas = HerramientaRepositoryDjango()
        self.historial = HistorialCostoRepositoryDjango()
        self.proveedores = ProveedorRepositoryDjango()
        self.movimientos = MovimientoRepositoryDjango()
        self.sucursales = SucursalRepositoryDjango()
        self.transferencias = TransferenciaRepositoryDjango()
        self.promociones = PromocionRepositoryDjango()

        if not reiniciar and HerramientaModel.objects.exists():
            self.stdout.write(self.style.WARNING(
                "Ya hay herramientas cargadas: no se hizo nada. Usa --reiniciar para reemplazar el inventario."
            ))
            return

        self.sucursales_activas = [s for s in self.sucursales.listar() if s.activa]
        if not self.sucursales_activas:
            raise CommandError("No hay sucursales activas: crea al menos una antes de cargar la demo.")
        self._elegir_actores()

        self.ahora = timezone.localtime()
        self.hoy = self.ahora.date()
        self.fotos_nuevas: list[str] = []
        try:
            with transaction.atomic():
                if reiniciar:
                    self._borrar_inventario()
                ids_proveedores = self._crear_proveedores()
                self.ids = self._crear_herramientas(ids_proveedores)
                self._cargar_movimientos()
                self._crear_promocion()
        except BaseException:
            # La base vuelve atrás sola; las fotos ya escritas en disco no.
            for nombre in self.fotos_nuevas:
                default_storage.delete(nombre)
            raise
        self._resumen()

    # --- Quién hace cada cosa -------------------------------------------

    def _elegir_actores(self) -> None:
        """El Administrador da de alta todo; en cada sucursal vende un
        Empleado de ahí y recibe un Supervisor de ahí (si no hay, lo hace
        el Administrador)."""
        usuarios = [u for u in UsuarioRepositoryDjango().listar() if u.activo]
        administradores = sorted((u for u in usuarios if u.rol == Rol.ADMINISTRADOR), key=lambda u: u.id)
        if not administradores:
            raise CommandError("No hay un Administrador activo: hace falta uno para registrar los datos.")
        self.admin = self._actor(administradores[0])

        def de_la_sucursal(sucursal_id, rol):
            elegidos = sorted((u for u in usuarios if u.rol == rol and u.sucursal_id == sucursal_id), key=lambda u: u.id)
            return self._actor(elegidos[0]) if elegidos else None

        self.vendedor, self.encargado = [], []
        for sucursal in self.sucursales_activas:
            encargado = de_la_sucursal(sucursal.id, Rol.SUPERVISOR) or self.admin
            self.encargado.append(encargado)
            self.vendedor.append(de_la_sucursal(sucursal.id, Rol.EMPLEADO) or encargado)

    @staticmethod
    def _actor(usuario) -> Actor:
        return Actor(usuario_id=usuario.id, rol=usuario.rol, sucursal_id=usuario.sucursal_id)

    # --- Fechas ------------------------------------------------------------

    def _momento(self, dia: int, minuto: int = 9 * 60) -> datetime:
        """Fecha y hora local de hace `dia` días; las de hoy, nunca después
        de ahora."""
        momento = timezone.make_aware(datetime.combine(self.hoy - timedelta(days=dia), time(minuto // 60, minuto % 60)))
        if dia == 0:
            momento = min(momento, self.ahora - timedelta(minutes=1))
        return momento

    @staticmethod
    def _fechar(modelo, pk: int, **fechas) -> None:
        # update() no dispara los signals: la auditoría guarda el alta tal
        # como la hizo el caso de uso, sin un UPDATE extra por la fecha.
        modelo.objects.filter(pk=pk).update(**fechas)

    # --- Pasos ---------------------------------------------------------------

    def _borrar_inventario(self) -> None:
        """Borra con el ORM (cada borrado queda en la auditoría). Primero
        lo que apunta a otras tablas. Las fotos se borran del disco solo si
        la transacción se confirma."""
        fotos = [n for n in HerramientaModel.objects.values_list("imagen", flat=True) if n]
        for modelo in (TransferenciaModel, PromocionModel, MovimientoModel, HistorialCostoModel,
                       HerramientaModel, ProveedorModel):
            modelo.objects.all().delete()
        transaction.on_commit(lambda: [default_storage.delete(n) for n in fotos])

    def _crear_proveedores(self) -> list[int]:
        ids = []
        for datos in PROVEEDORES:
            proveedor = registrar_proveedor(self.proveedores, self.admin, datos)
            self._fechar(ProveedorModel, proveedor.id, creado_en=self._momento(DIAS_DE_HISTORIA + 10))
            ids.append(proveedor.id)
        return ids

    def _crear_herramientas(self, ids_proveedores: list[int]) -> dict[str, int]:
        ids = {}
        for semilla, demo in enumerate(HERRAMIENTAS):
            contenido = dibujar(demo.dibujo, semilla)
            datos = {
                "codigo": demo.codigo,
                "nombre": demo.nombre,
                "modelo": demo.modelo,
                "unidades_por_caja": demo.unidades_por_caja,
                "demanda_anual": demo.demanda_anual,
                "costo_pedido": Decimal(demo.costo_pedido),
                "costo_almacenamiento_unitario": Decimal(demo.costo_almacenamiento),
                "tiempo_entrega_dias": demo.tiempo_entrega_dias,
                "costo_unitario": Decimal(demo.costo_anterior or demo.costo),
                "proveedor_id": ids_proveedores[demo.proveedor],
            }
            imagen = ImagenProducto(
                nombre=f"{demo.codigo}.png", formato="PNG", tamano_bytes=len(contenido), contenido=ContentFile(contenido)
            )
            herramienta = gestionar_herramientas.registrar_herramienta(
                self.herramientas, datos, actor=self.admin, historial=self.historial,
                proveedores=self.proveedores, imagen=imagen,
            )
            self.fotos_nuevas.append(herramienta.imagen)
            if demo.costo_anterior:
                gestionar_herramientas.actualizar_herramienta(
                    self.herramientas, herramienta.id, {"costo_unitario": Decimal(demo.costo)},
                    actor=self.admin, historial=self.historial, proveedores=self.proveedores,
                )
            alta, *cambios = HistorialCostoModel.objects.filter(herramienta_id=herramienta.id).order_by("id")
            self._fechar(HistorialCostoModel, alta.id, fecha=self._momento(DIAS_DE_HISTORIA + 5))
            for cambio in cambios:
                self._fechar(HistorialCostoModel, cambio.id, fecha=self._momento(120, 11 * 60))
            self._fechar(HerramientaModel, herramienta.id, creado_en=self._momento(DIAS_DE_HISTORIA + 5))
            ids[demo.codigo] = herramienta.id
        return ids

    def _cargar_movimientos(self) -> None:
        rng = random.Random(SEMILLA)
        n = len(self.sucursales_activas)
        eventos = [e for demo in HERRAMIENTAS for e in planificar(demo, n, rng)]
        eventos.sort(key=lambda e: (-e.dia, e.minuto, e.codigo, e.secuencia))
        for evento in eventos:
            momento = self._momento(evento.dia, evento.minuto)
            herramienta_id = self.ids[evento.codigo]
            sucursal_id = self.sucursales_activas[evento.sucursal].id
            if evento.tipo in ("entrada", "salida"):
                registrar = registrar_entrada if evento.tipo == "entrada" else registrar_salida
                actor = (self.encargado if evento.tipo == "entrada" else self.vendedor)[evento.sucursal]
                unidad = TipoUnidad.CAJA if evento.tipo == "entrada" else TipoUnidad.UNIDAD
                movimiento = registrar(self.movimientos, self.herramientas, self.sucursales, actor,
                                       herramienta_id, sucursal_id, unidad, evento.cantidad)
                self._fechar(MovimientoModel, movimiento.id, creado_en=momento)
            else:
                self._transferir(evento, herramienta_id, sucursal_id, momento)

    def _transferir(self, evento: Evento, herramienta_id: int, origen_id: int, momento: datetime) -> None:
        """La pide el encargado de la sucursal de origen y la resuelve el
        Administrador."""
        destino_id = self.sucursales_activas[evento.destino].id
        transferencia = gestionar_transferencias.solicitar_transferencia(
            self.transferencias, self.movimientos, self.herramientas, self.sucursales, self.encargado[0],
            herramienta_id, origen_id, destino_id, TipoUnidad.UNIDAD, evento.cantidad,
        )
        if evento.tipo == "transferencia":
            transferencia = gestionar_transferencias.completar_transferencia(
                self.transferencias, self.movimientos, self.herramientas, self.sucursales,
                self.admin, transferencia.id, momento,
            )
            for movimiento_id in (transferencia.movimiento_salida_id, transferencia.movimiento_entrada_id):
                self._fechar(MovimientoModel, movimiento_id, creado_en=momento)
        elif evento.tipo == "rechazada":
            gestionar_transferencias.rechazar_transferencia(
                self.transferencias, self.admin, transferencia.id, MOTIVO_RECHAZO, momento + timedelta(hours=2),
            )
        self._fechar(TransferenciaModel, transferencia.id, creado_en=momento - timedelta(hours=3))

    def _crear_promocion(self) -> None:
        crear_promocion(
            self.promociones, self.movimientos, self.herramientas, self.sucursales, self.admin,
            {
                "herramienta_id": self.ids[PROMOCION["codigo"]],
                "sucursal_id": self.sucursales_activas[0].id,
                "descuento_porcentaje": PROMOCION["descuento_porcentaje"],
                "fecha_fin": self.hoy + timedelta(days=PROMOCION["dias"]),
                "motivo": PROMOCION["motivo"],
            },
            self.hoy,
        )

    def _resumen(self) -> None:
        conteo = {
            "Proveedores": ProveedorModel.objects.count(),
            "Herramientas (con foto)": HerramientaModel.objects.exclude(imagen="").count(),
            "Cambios de costo": HistorialCostoModel.objects.count(),
            "Movimientos": MovimientoModel.objects.count(),
            "Transferencias": TransferenciaModel.objects.count(),
            "Promociones": PromocionModel.objects.count(),
        }
        for tipo in ("ENTRADA", "SALIDA", "TRANSFERENCIA_SALIDA", "TRANSFERENCIA_ENTRADA"):
            conteo[f"  {tipo.lower().replace('_', ' ')}"] = MovimientoModel.objects.filter(tipo_movimiento=tipo).count()
        nombres = ", ".join(s.nombre for s in self.sucursales_activas)
        self.stdout.write(self.style.SUCCESS(f"Datos de ejemplo cargados en: {nombres}."))
        for etiqueta, cantidad in conteo.items():
            self.stdout.write(f"  {etiqueta}: {cantidad}")
