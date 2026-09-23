"""
Pruebas de las fórmulas puras de indicadores. Usan SimpleTestCase (sin
base de datos) porque domain/formulas.py no depende de Django ni del ORM.

Correr con: python manage.py test apps.indicadores
"""

from django.test import SimpleTestCase

from .domain.formulas import (
    ajustar_a_cajas,
    cajas_a_unidades,
    calcular_eoq,
    calcular_rop,
    unidades_a_cajas,
)


class CalcularEOQTests(SimpleTestCase):
    def test_formula_basica(self):
        # raiz(2 * 1000 * 50 / 2) = raiz(50000) = 223.606...
        self.assertAlmostEqual(calcular_eoq(1000, 50, 2), 223.6068, places=4)

    def test_sin_costo_almacenamiento_devuelve_none(self):
        self.assertIsNone(calcular_eoq(1000, 50, 0))
        self.assertIsNone(calcular_eoq(1000, 50, None))

    def test_dato_faltante_devuelve_none(self):
        self.assertIsNone(calcular_eoq(None, 50, 2))
        self.assertIsNone(calcular_eoq(1000, None, 2))

    def test_demanda_negativa_es_error(self):
        with self.assertRaises(ValueError):
            calcular_eoq(-1, 50, 2)


class CalcularROPTests(SimpleTestCase):
    def test_formula_basica(self):
        # (730 / 365) * 10 = 20
        self.assertAlmostEqual(calcular_rop(730, 10), 20.0)

    def test_dato_faltante_devuelve_none(self):
        self.assertIsNone(calcular_rop(730, None))
        self.assertIsNone(calcular_rop(None, 10))

    def test_negativo_es_error(self):
        with self.assertRaises(ValueError):
            calcular_rop(730, -1)


class ConversionCajaUnidadTests(SimpleTestCase):
    def test_ajustar_a_cajas_redondea_hacia_arriba(self):
        self.assertEqual(ajustar_a_cajas(30, 12), 36)
        self.assertEqual(ajustar_a_cajas(24, 12), 24)
        self.assertEqual(ajustar_a_cajas(223.6, 12), 228)

    def test_ajustar_a_cajas_sin_factor_valido(self):
        self.assertEqual(ajustar_a_cajas(30, None), 30)
        self.assertEqual(ajustar_a_cajas(30, 0), 30)

    def test_cajas_a_unidades(self):
        self.assertEqual(cajas_a_unidades(3, 12), 36)
        with self.assertRaises(ValueError):
            cajas_a_unidades(3, 0)

    def test_unidades_a_cajas(self):
        self.assertEqual(unidades_a_cajas(30, 12), (2, 6))
        with self.assertRaises(ValueError):
            unidades_a_cajas(-1, 12)


# --- Panel de auditoría (HU24) ---

from datetime import date, datetime, timedelta, timezone as dt_timezone

from rest_framework.test import APITestCase

from apps.catalogo.domain.entities import Herramienta
from apps.movimientos.domain.entities import ResumenInventario
from apps.movimientos.domain.value_objects import TipoMovimiento as T
from apps.usuarios.domain.entities import Sucursal

from .use_cases.panel_auditoria import construir_panel

HOY = date(2026, 9, 22)


def hace(dias: int) -> datetime:
    return datetime.combine(HOY - timedelta(days=dias), datetime.min.time(), tzinfo=dt_timezone.utc)


class _Repo:
    def __init__(self, datos):
        self.datos = datos

    def listar(self):
        return self.datos

    def resumen_inventario(self):
        return self.datos


def herramienta(id, demanda=None, entrega=None, costo_pedido=None, costo_alm=None, caja=1):
    return Herramienta(id=id, codigo=f"H-{id}", nombre=f"Herramienta {id}", modelo="",
                       unidades_por_caja=caja, demanda_anual=demanda, tiempo_entrega_dias=entrega,
                       costo_pedido=costo_pedido, costo_almacenamiento_unitario=costo_alm)


def resumen(h, s, entradas=0, salidas=0, primero=100, ultima_salida=None, ajuste_neg=0):
    return ResumenInventario(h, s, {T.ENTRADA: entradas, T.SALIDA: salidas, T.AJUSTE_NEGATIVO: ajuste_neg},
                             hace(primero), None if ultima_salida is None else hace(ultima_salida))


class PanelAuditoriaUseCaseTests(SimpleTestCase):
    sucursales = _Repo([Sucursal(1, "Central", ""), Sucursal(2, "Norte", ""), Sucursal(3, "Cerrada", "", activa=False)])

    def _panel(self, herramientas, filas):
        return construir_panel(_Repo(filas), _Repo(herramientas), self.sucursales, hoy=HOY)

    def test_alerta_de_reorden_con_stock_de_ambas_sucursales_y_pedido_en_cajas(self):
        # ROP = 730/365 * 10 = 20; stock total 10 + 5 = 15 <= 20 -> alerta.
        # EOQ = raiz(2*730*50/2) = 191.05 -> 16 cajas de 12 = 192.
        panel = self._panel(
            [herramienta(1, demanda=730, entrega=10, costo_pedido=50, costo_alm=2, caja=12)],
            [resumen(1, 1, entradas=10, ultima_salida=1), resumen(1, 2, entradas=5, ultima_salida=1)],
        )
        self.assertEqual(panel.total_alertas_stock, 1)
        alerta = panel.alertas[0]
        self.assertEqual((alerta.stock_total, alerta.punto_reorden, alerta.pedido_sugerido), (15, 20.0, 192))

    def test_sin_alerta_si_el_stock_supera_el_rop_y_sin_datos_se_informa(self):
        panel = self._panel(
            [herramienta(1, demanda=730, entrega=10), herramienta(2)],
            [resumen(1, 1, entradas=25, ultima_salida=1)],
        )
        self.assertEqual((panel.total_alertas_stock, panel.herramientas_sin_datos_rop), (0, 1))

    def test_alerta_sin_costos_no_tiene_pedido_sugerido(self):
        panel = self._panel([herramienta(1, demanda=730, entrega=10)], [])
        self.assertEqual(panel.alertas[0].stock_total, 0)
        self.assertIsNone(panel.alertas[0].pedido_sugerido)

    def test_estancamiento_por_ultima_venta(self):
        panel = self._panel(
            [herramienta(1), herramienta(2), herramienta(3)],
            [
                resumen(1, 1, entradas=5, ultima_salida=41),               # 41 > 40 -> estancada
                resumen(2, 1, entradas=5, ultima_salida=40),               # 40, no supera
                resumen(3, 1, entradas=5, salidas=5, ultima_salida=90),    # sin stock -> no
            ],
        )
        self.assertEqual([(e.herramienta_id, e.dias_sin_venta, e.nunca_vendida) for e in panel.estancadas],
                         [(1, 41, False)])

    def test_nunca_vendida_cuenta_desde_su_primer_movimiento(self):
        panel = self._panel(
            [herramienta(1), herramienta(2)],
            [resumen(1, 2, entradas=3, primero=50), resumen(2, 2, entradas=3, primero=5)],
        )
        self.assertEqual([(e.herramienta_id, e.sucursal_nombre, e.nunca_vendida) for e in panel.estancadas],
                         [(1, "Norte", True)])

    def test_totales_y_orden(self):
        panel = self._panel(
            [herramienta(1), herramienta(2), herramienta(3)],
            [resumen(1, 1, entradas=5, ultima_salida=45), resumen(2, 1, entradas=5, ultima_salida=90)],
        )
        self.assertEqual((panel.total_herramientas, panel.total_sucursales_activas), (3, 2))
        self.assertEqual([e.herramienta_id for e in panel.estancadas], [2, 1])  # más días primero


class PanelAuditoriaApiTests(APITestCase):
    def setUp(self):
        from apps.catalogo.infrastructure.models import Herramienta as HerramientaModel
        from apps.movimientos.infrastructure.models import Movimiento
        from apps.usuarios.infrastructure.models import Sucursal as SucursalModel, Usuario

        self.Movimiento = Movimiento
        self.central = SucursalModel.objects.create(nombre="Central")
        self.h = HerramientaModel.objects.create(codigo="T-1", nombre="Taladro", demanda_anual=730, tiempo_entrega_dias=10)
        self.sup = Usuario.objects.create_user("sup", password="x", rol="SUPERVISOR", sucursal=self.central)
        self.emp = Usuario.objects.create_user("emp", password="x", rol="EMPLEADO", sucursal=self.central)

    def _mov(self, tipo, cantidad, dias_atras):
        from django.utils import timezone
        m = self.Movimiento.objects.create(herramienta=self.h, sucursal=self.central, usuario=self.sup,
                                           tipo_movimiento=tipo, tipo_unidad="UNIDAD", cantidad=cantidad,
                                           cantidad_unidades=cantidad, motivo="x" if "AJUSTE" in tipo else "")
        # creado_en es auto_now_add: se mueve al pasado con update() para simular antigüedad.
        self.Movimiento.objects.filter(pk=m.pk).update(creado_en=timezone.now() - timedelta(days=dias_atras))

    def test_panel_con_datos_reales(self):
        self._mov("ENTRADA", 30, dias_atras=100)
        self._mov("SALIDA", 5, dias_atras=60)
        # Un ajuste reciente NO es una venta: no reinicia los días sin venta.
        self._mov("AJUSTE_NEGATIVO", 10, dias_atras=1)
        self.client.force_authenticate(self.emp)  # todos los roles ven el panel
        respuesta = self.client.get("/api/indicadores/panel/")
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        # stock = 30 - 5 - 10 = 15 <= ROP 20 -> alerta
        self.assertEqual(datos["total_alertas_stock"], 1)
        self.assertEqual(datos["alertas"][0]["stock_total"], 15)
        self.assertEqual(datos["total_herramientas_estancadas"], 1)
        self.assertEqual(datos["estancadas"][0]["dias_sin_venta"], 60)
        self.assertEqual((datos["total_herramientas"], datos["total_sucursales_activas"]), (1, 1))

    def test_sin_sesion_es_401(self):
        self.assertEqual(self.client.get("/api/indicadores/panel/").status_code, 401)
