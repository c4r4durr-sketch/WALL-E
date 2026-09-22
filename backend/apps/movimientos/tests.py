"""
Pruebas de movimientos:
  - use_cases con repositorios en memoria (sin base de datos);
  - la API: entradas, salidas, conversión caja->unidad, stock insuficiente,
    stock por sucursal, historial, inmutabilidad y permisos por rol.

Correr con: python manage.py test apps.movimientos
"""

from dataclasses import replace
from typing import Optional

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.catalogo.domain.entities import Herramienta
from apps.catalogo.infrastructure.models import Herramienta as HerramientaModel
from apps.usuarios.domain.entities import Actor, Sucursal
from apps.usuarios.infrastructure.models import Sucursal as SucursalModel
from apps.usuarios.infrastructure.models import Usuario

from .domain.entities import Movimiento
from .domain.exceptions import (
    HerramientaInexistenteError,
    StockInsuficienteError,
    SucursalInvalidaError,
    SucursalNoPermitidaError,
)
from .domain.stock import stock_desde_totales
from .domain.value_objects import TipoMovimiento
from .infrastructure.models import Movimiento as MovimientoModel
from .use_cases import registrar_movimiento as casos

URL = "/api/movimientos/"


# --- Repositorios falsos en memoria para probar los use_cases ---

class MovimientosEnMemoria:
    def __init__(self):
        self.datos: list[Movimiento] = []
        self.bloqueos: list[int] = []

    def obtener_por_id(self, movimiento_id):
        return next((m for m in self.datos if m.id == movimiento_id), None)

    def listar(self, herramienta_id=None, sucursal_id=None):
        return [m for m in self.datos
                if herramienta_id in (None, m.herramienta_id) and sucursal_id in (None, m.sucursal_id)]

    def unidades_por_tipo(self, herramienta_id, sucursal_id):
        totales: dict[TipoMovimiento, int] = {}
        for m in self.listar(herramienta_id, sucursal_id):
            totales[m.tipo_movimiento] = totales.get(m.tipo_movimiento, 0) + m.cantidad_unidades
        return totales

    def bloquear_stock(self, herramienta_id):
        self.bloqueos.append(herramienta_id)

    def guardar(self, movimiento):
        movimiento = replace(movimiento, id=len(self.datos) + 1)
        self.datos.append(movimiento)
        return movimiento


class HerramientasEnMemoria:
    def __init__(self, *herramientas: Herramienta):
        self.datos = {h.id: h for h in herramientas}

    def obtener_por_id(self, herramienta_id) -> Optional[Herramienta]:
        return self.datos.get(herramienta_id)


class SucursalesEnMemoria:
    def __init__(self, *sucursales: Sucursal):
        self.datos = {s.id: s for s in sucursales}

    def obtener_por_id(self, sucursal_id):
        return self.datos.get(sucursal_id)

    def listar(self):
        return list(self.datos.values())


class StockDominioTests(SimpleTestCase):
    def test_entradas_suman_salidas_restan(self):
        self.assertEqual(stock_desde_totales({TipoMovimiento.ENTRADA: 50, TipoMovimiento.SALIDA: 12}), 38)
        self.assertEqual(stock_desde_totales({}), 0)


class RegistrarMovimientoUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.movs = MovimientosEnMemoria()
        self.herrs = HerramientasEnMemoria(Herramienta(id=1, codigo="T", nombre="Taladro", modelo="", unidades_por_caja=12))
        self.sucs = SucursalesEnMemoria(
            Sucursal(id=1, nombre="Central", direccion=""),
            Sucursal(id=2, nombre="Norte", direccion=""),
            Sucursal(id=3, nombre="Cerrada", direccion="", activa=False),
        )
        self.admin = Actor(usuario_id=1, rol="ADMINISTRADOR", sucursal_id=None)
        self.empleado = Actor(usuario_id=2, rol="EMPLEADO", sucursal_id=1)

    def _entrada(self, actor=None, sucursal=1, unidad="UNIDAD", cantidad=10, herramienta=1):
        return casos.registrar_entrada(self.movs, self.herrs, self.sucs, actor or self.admin,
                                       herramienta, sucursal, unidad, cantidad)

    def _salida(self, actor=None, sucursal=1, unidad="UNIDAD", cantidad=1):
        return casos.registrar_salida(self.movs, self.herrs, self.sucs, actor or self.admin,
                                      1, sucursal, unidad, cantidad)

    def test_entrada_en_cajas_se_convierte_a_unidades(self):
        movimiento = self._entrada(unidad="CAJA", cantidad=2)
        self.assertEqual((movimiento.cantidad, movimiento.cantidad_unidades), (2, 24))

    def test_salida_con_stock_suficiente_y_exacto(self):
        self._entrada(cantidad=10)
        self._salida(cantidad=4)
        self._salida(cantidad=6)  # deja el stock exactamente en 0
        self.assertEqual(casos.consultar_stock(self.movs, self.herrs, self.sucs, 1, 1)[0].unidades, 0)

    def test_salida_sin_stock_suficiente(self):
        self._entrada(cantidad=10)
        with self.assertRaises(StockInsuficienteError) as ctx:
            self._salida(unidad="CAJA", cantidad=1)  # 12 unidades > 10
        self.assertEqual((ctx.exception.disponible, ctx.exception.solicitado), (10, 12))
        self.assertEqual(len(self.movs.datos), 1)  # no se guardó la salida

    def test_el_stock_es_por_sucursal(self):
        self._entrada(sucursal=2, cantidad=10)
        with self.assertRaises(StockInsuficienteError):
            self._salida(sucursal=1, cantidad=1)

    def test_salida_bloquea_el_stock_antes_de_validar(self):
        self._entrada(cantidad=5)
        self._salida(cantidad=1)
        self.assertEqual(self.movs.bloqueos, [1])

    def test_empleado_solo_en_su_sucursal(self):
        self._entrada(actor=self.empleado, sucursal=1)
        with self.assertRaises(SucursalNoPermitidaError):
            self._entrada(actor=self.empleado, sucursal=2)

    def test_herramienta_o_sucursal_invalida(self):
        with self.assertRaises(HerramientaInexistenteError):
            self._entrada(herramienta=99)
        with self.assertRaises(SucursalInvalidaError):
            self._entrada(sucursal=3)  # inactiva
        with self.assertRaises(SucursalInvalidaError):
            self._entrada(sucursal=99)

    def test_consultar_stock_en_todas_las_sucursales_activas(self):
        self._entrada(sucursal=1, unidad="CAJA", cantidad=2)
        self._entrada(sucursal=1, cantidad=5)
        stock = casos.consultar_stock(self.movs, self.herrs, self.sucs, 1)
        self.assertEqual([(s.sucursal_id, s.unidades, s.cajas_completas, s.unidades_sueltas) for s in stock],
                         [(1, 29, 2, 5), (2, 0, 0, 0)])


class MovimientoApiTests(APITestCase):
    def setUp(self):
        self.central = SucursalModel.objects.create(nombre="Central")
        self.norte = SucursalModel.objects.create(nombre="Norte")
        self.herramienta = HerramientaModel.objects.create(codigo="T-1", nombre="Taladro", unidades_por_caja=12)
        self.admin = Usuario.objects.create_user("admin_t", password="x", rol="ADMINISTRADOR")
        self.supervisor = Usuario.objects.create_user("sup_t", password="x", rol="SUPERVISOR", sucursal=self.central)
        self.empleado = Usuario.objects.create_user("emp_t", password="x", rol="EMPLEADO", sucursal=self.central)
        self.client.force_authenticate(self.admin)

    def _registrar(self, tipo="ENTRADA", unidad="UNIDAD", cantidad=10, sucursal=None, herramienta=None):
        return self.client.post(URL, {
            "herramienta": herramienta or self.herramienta.id,
            "sucursal": sucursal or self.central.id,
            "tipo_movimiento": tipo, "tipo_unidad": unidad, "cantidad": cantidad,
        }, format="json")

    def _stock(self, sucursal=None):
        params = {"herramienta": self.herramienta.id}
        if sucursal:
            params["sucursal"] = sucursal
        return self.client.get(f"{URL}stock/", params)

    def test_entrada_en_cajas_guarda_unidades_y_usuario(self):
        respuesta = self._registrar(unidad="CAJA", cantidad=2)
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertEqual((datos["cantidad"], datos["tipo_unidad"], datos["cantidad_unidades"]), (2, "CAJA", 24))
        self.assertEqual(datos["usuario_username"], "admin_t")

    def test_salida_mayor_al_stock_es_400_con_mensaje_claro(self):
        self._registrar(cantidad=10)
        respuesta = self._registrar(tipo="SALIDA", unidad="CAJA", cantidad=1)
        self.assertEqual(respuesta.status_code, 400)
        mensaje = respuesta.json()["cantidad"][0]
        self.assertIn("Stock insuficiente", mensaje)
        self.assertIn("10", mensaje)
        self.assertIn("12", mensaje)
        self.assertEqual(MovimientoModel.objects.filter(tipo_movimiento="SALIDA").count(), 0)

    def test_salida_valida_descuenta_stock(self):
        self._registrar(unidad="CAJA", cantidad=3)  # 36
        self.assertEqual(self._registrar(tipo="SALIDA", cantidad=10).status_code, 201)
        stock = self._stock(self.central.id).json()[0]
        self.assertEqual((stock["unidades"], stock["cajas_completas"], stock["unidades_sueltas"]), (26, 2, 2))

    def test_stock_en_ambas_sucursales(self):
        self._registrar(cantidad=5, sucursal=self.norte.id)
        stock = {s["sucursal_nombre"]: s["unidades"] for s in self._stock().json()}
        self.assertEqual(stock, {"Central": 0, "Norte": 5})

    def test_cambiar_caja_en_catalogo_no_altera_stock_historico(self):
        self._registrar(unidad="CAJA", cantidad=2)  # 24 con cajas de 12
        self.client.patch(f"/api/catalogo/herramientas/{self.herramienta.id}/", {"unidades_por_caja": 6}, format="json")
        self.assertEqual(self._stock(self.central.id).json()[0]["unidades"], 24)

    def test_historial_por_herramienta(self):
        otra = HerramientaModel.objects.create(codigo="A-1", nombre="Amoladora")
        self._registrar(cantidad=5)
        self._registrar(tipo="SALIDA", cantidad=2)
        self._registrar(cantidad=1, herramienta=otra.id)
        historial = self.client.get(URL, {"herramienta": self.herramienta.id}).json()
        self.assertEqual([m["tipo_movimiento"] for m in historial], ["SALIDA", "ENTRADA"])  # más reciente primero

    def test_datos_invalidos(self):
        self.assertIn("herramienta", self._registrar(herramienta=999).json())
        self.assertEqual(self._registrar(cantidad=0).status_code, 400)
        self.assertEqual(self._registrar(unidad="PALET").status_code, 400)
        self.assertEqual(self._stock_de(999).status_code, 404)

    def _stock_de(self, herramienta_id):
        return self.client.get(f"{URL}stock/", {"herramienta": herramienta_id})

    def test_nadie_puede_editar_ni_borrar_movimientos(self):
        movimiento_id = self._registrar().json()["id"]
        detalle = f"{URL}{movimiento_id}/"
        for usuario in [self.admin, self.supervisor, self.empleado]:
            self.client.force_authenticate(usuario)
            with self.subTest(rol=usuario.rol):
                self.assertEqual(self.client.put(detalle, {"cantidad": 1}, format="json").status_code, 405)
                self.assertEqual(self.client.patch(detalle, {"cantidad": 1}, format="json").status_code, 405)
                self.assertEqual(self.client.delete(detalle).status_code, 405)
        self.assertEqual(MovimientoModel.objects.get(pk=movimiento_id).cantidad, 10)

    def test_empleado_registra_en_su_sucursal_pero_no_en_otra(self):
        self.client.force_authenticate(self.empleado)
        self.assertEqual(self._registrar(sucursal=self.central.id).status_code, 201)
        self.assertEqual(self._registrar(sucursal=self.norte.id).status_code, 403)
        self.assertEqual(self.client.get(URL).status_code, 200)

    def test_sin_sesion_es_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(URL).status_code, 401)
        self.assertEqual(self._registrar().status_code, 401)
