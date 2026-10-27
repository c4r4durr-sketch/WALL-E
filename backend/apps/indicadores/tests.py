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

    def test_dias_sin_venta_se_cuentan_en_hora_de_la_paz(self):
        # Venta a las 22:00 de La Paz hace 41 días: en UTC ya es el día
        # siguiente (02:00), y contando en UTC saldrían 40 días (no estancada).
        from datetime import datetime, time
        from django.utils import timezone
        la_paz = timezone.get_current_timezone()
        venta = datetime.combine(timezone.localdate() - timedelta(days=41), time(22, 0), tzinfo=la_paz)
        self._mov("ENTRADA", 10, dias_atras=100)
        self._mov("SALIDA", 1, dias_atras=0)
        self.Movimiento.objects.filter(tipo_movimiento="SALIDA").update(creado_en=venta)
        self.client.force_authenticate(self.emp)
        datos = self.client.get("/api/indicadores/panel/").json()
        self.assertEqual(datos["total_herramientas_estancadas"], 1)
        self.assertEqual(datos["estancadas"][0]["dias_sin_venta"], 41)

    def test_sin_sesion_es_401(self):
        self.assertEqual(self.client.get("/api/indicadores/panel/").status_code, 401)


# --- EOQ / ROP / ABC (paso 4.5) ---

from .use_cases.calcular_eoq import resultado_eoq
from .use_cases.calcular_punto_reorden import resultado_rop
from .use_cases.clasificar_abc import clasificar


class EOQUseCaseTests(SimpleTestCase):
    def test_eoq_completo_y_ajustado_a_cajas(self):
        # raiz(2*730*120/8) = 147.99 -> cajas de 6: 25 cajas = 150
        r = resultado_eoq(herramienta(1, demanda=730, costo_pedido=120, costo_alm=8, caja=6), demanda_observada=500)
        self.assertEqual((r.eoq, r.eoq_ajustado_cajas, r.demanda_observada, r.datos_faltantes), (147.99, 150, 500, ()))

    def test_datos_faltantes(self):
        r = resultado_eoq(herramienta(1, demanda=730))
        self.assertIsNone(r.eoq)
        self.assertEqual(r.datos_faltantes, ("costo_pedido", "costo_almacenamiento_unitario"))
        r = resultado_eoq(herramienta(1, demanda=730, costo_pedido=10, costo_alm=0))
        self.assertEqual(r.datos_faltantes, ("costo_almacenamiento_unitario",))


class ROPUseCaseTests(SimpleTestCase):
    def test_rop_y_requiere_reorden(self):
        r = resultado_rop(herramienta(1, demanda=730, entrega=15), stock_total=30)
        self.assertEqual((r.punto_reorden, r.demanda_diaria_promedio, r.requiere_reorden), (30.0, 2.0, True))
        self.assertFalse(resultado_rop(herramienta(1, demanda=730, entrega=15), stock_total=31).requiere_reorden)

    def test_sin_datos_no_hay_alerta(self):
        r = resultado_rop(herramienta(1, demanda=730), stock_total=0)
        self.assertEqual((r.punto_reorden, r.requiere_reorden, r.datos_faltantes), (None, False, ("tiempo_entrega_dias",)))


class ClasificacionABCTests(SimpleTestCase):
    def test_regla_80_95(self):
        # 50 / 30 / 15 / 5 -> A A B C ; la sin ventas siempre C
        hs = [herramienta(i) for i in range(1, 6)]
        r = clasificar(hs, {1: 50, 2: 30, 3: 15, 4: 5})
        self.assertEqual([(c.herramienta_id, c.clase) for c in r], [(1, "A"), (2, "A"), (3, "B"), (4, "C"), (5, "C")])
        self.assertEqual([c.porcentaje_acumulado for c in r], [50.0, 80.0, 95.0, 100.0, 100.0])

    def test_la_mas_vendida_siempre_es_a(self):
        r = clasificar([herramienta(1), herramienta(2)], {1: 90, 2: 10})
        self.assertEqual([c.clase for c in r], ["A", "B"])

    def test_sin_ventas_todas_c(self):
        r = clasificar([herramienta(1), herramienta(2)], {})
        self.assertEqual([(c.clase, c.porcentaje) for c in r], [("C", 0.0), ("C", 0.0)])


class IndicadoresApiTests(APITestCase):
    def setUp(self):
        from apps.catalogo.infrastructure.models import Herramienta as HerramientaModel
        from apps.movimientos.infrastructure.models import Movimiento
        from apps.usuarios.infrastructure.models import Sucursal as SucursalModel, Usuario

        self.Movimiento = Movimiento
        self.central = SucursalModel.objects.create(nombre="Central")
        self.norte = SucursalModel.objects.create(nombre="Norte")
        self.u = Usuario.objects.create_user("emp", password="x", rol="EMPLEADO", sucursal=self.central)
        self.tal = HerramientaModel.objects.create(codigo="TAL", nombre="Taladro", unidades_por_caja=6,
                                                   demanda_anual=730, tiempo_entrega_dias=15,
                                                   costo_pedido=120, costo_almacenamiento_unitario=8)
        self.amo = HerramientaModel.objects.create(codigo="AMO", nombre="Amoladora")
        self.client.force_authenticate(self.u)

    def _mov(self, h, tipo, n, sucursal=None, dias_atras=0):
        from django.utils import timezone
        m = self.Movimiento.objects.create(herramienta=h, sucursal=sucursal or self.central, usuario=self.u,
                                           tipo_movimiento=tipo, tipo_unidad="UNIDAD", cantidad=n,
                                           cantidad_unidades=n, motivo="x" if "AJUSTE" in tipo else "")
        self.Movimiento.objects.filter(pk=m.pk).update(creado_en=timezone.now() - timedelta(days=dias_atras))

    def test_eoq_con_demanda_observada_de_12_meses(self):
        self._mov(self.tal, "ENTRADA", 100, dias_atras=400)
        self._mov(self.tal, "SALIDA", 40, dias_atras=10)
        self._mov(self.tal, "SALIDA", 7, dias_atras=400)            # fuera del período
        self._mov(self.tal, "AJUSTE_NEGATIVO", 5, dias_atras=3)     # no es venta
        self._mov(self.tal, "TRANSFERENCIA_SALIDA", 8, dias_atras=3)  # no es venta
        datos = self.client.get(f"/api/indicadores/eoq/{self.tal.id}/").json()
        self.assertEqual((datos["eoq"], datos["eoq_ajustado_cajas"], datos["demanda_observada"]), (147.99, 150, 40))

    def test_eoq_con_datos_faltantes_es_200(self):
        respuesta = self.client.get(f"/api/indicadores/eoq/{self.amo.id}/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(respuesta.json()["eoq"])
        self.assertIn("demanda_anual", respuesta.json()["datos_faltantes"])

    def test_rop_con_stock_de_ambas_sucursales(self):
        self._mov(self.tal, "ENTRADA", 20)
        self._mov(self.tal, "ENTRADA", 10, sucursal=self.norte)
        datos = self.client.get(f"/api/indicadores/rop/{self.tal.id}/").json()
        self.assertEqual((datos["punto_reorden"], datos["stock_total"], datos["requiere_reorden"]), (30.0, 30, True))

    def test_abc(self):
        self._mov(self.tal, "ENTRADA", 100, dias_atras=30)
        self._mov(self.tal, "SALIDA", 30, dias_atras=5)
        datos = self.client.get("/api/indicadores/abc/").json()
        self.assertEqual([(d["codigo"], d["clase"], d["unidades_vendidas"]) for d in datos],
                         [("TAL", "A", 30), ("AMO", "C", 0)])

    def test_404_y_401(self):
        self.assertEqual(self.client.get("/api/indicadores/eoq/999/").status_code, 404)
        self.assertEqual(self.client.get("/api/indicadores/rop/999/").status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/indicadores/abc/").status_code, 401)


# --- Cierre diario (HU14) ---

from datetime import date as _date, datetime as _datetime, time as _time

from apps.catalogo.domain.entities import Herramienta as _Herramienta
from apps.movimientos.domain.entities import Movimiento as _Movimiento
from apps.movimientos.domain.value_objects import TipoMovimiento as _Tipo, TipoUnidad as _Unidad
from apps.usuarios.domain.entities import Actor as _Actor, Sucursal as _Sucursal
from apps.usuarios.domain.value_objects import Rol as _Rol

from .domain.exceptions import FechaFuturaError, ReporteNoPermitidoError, SucursalInexistenteError
from .use_cases.cierre_diario import construir_cierre

_HOY = _date(2026, 10, 20)


class _MovimientosDelDia:
    def __init__(self, movimientos):
        self.movimientos = movimientos
        self.pedidos = []

    def listar_del_dia(self, sucursal_id, fecha):
        self.pedidos.append((sucursal_id, fecha))
        return [m for m in self.movimientos if m.sucursal_id == sucursal_id]


class _Catalogo:
    def __init__(self):
        self.llamadas = 0

    def listar(self):
        self.llamadas += 1
        return [_Herramienta(1, "T-1", "Taladro", "", 12), _Herramienta(2, "M-1", "Martillo", "", 1)]


class _Sucursales:
    def obtener_por_id(self, sucursal_id):
        return {1: _Sucursal(1, "Central", ""), 2: _Sucursal(2, "Norte", "")}.get(sucursal_id)


def _mov(id, tipo, unidades, herramienta=1, sucursal=1, motivo=""):
    return _Movimiento(id=id, herramienta_id=herramienta, sucursal_id=sucursal, tipo_movimiento=tipo,
                       tipo_unidad=_Unidad.UNIDAD, cantidad=unidades, cantidad_unidades=unidades,
                       usuario_id=1, motivo=motivo, creado_en=_datetime(2026, 10, 20, 10, id),
                       usuario_username="ana")


_ADMIN = _Actor(usuario_id=1, rol=_Rol.ADMINISTRADOR, sucursal_id=None)
_SUP_CENTRAL = _Actor(usuario_id=2, rol=_Rol.SUPERVISOR, sucursal_id=1)
_EMPLEADO = _Actor(usuario_id=3, rol=_Rol.EMPLEADO, sucursal_id=1)


class CierreDiarioUseCaseTests(SimpleTestCase):
    def _cierre(self, movimientos, actor=_ADMIN, sucursal_id=1, fecha=_HOY):
        self.repo = _MovimientosDelDia(movimientos)
        self.catalogo = _Catalogo()
        return construir_cierre(self.repo, self.catalogo, _Sucursales(), actor, sucursal_id, fecha, hoy=_HOY)

    def test_totales_por_tipo_y_salidas_destacadas(self):
        cierre = self._cierre([
            _mov(1, _Tipo.ENTRADA, 24),
            _mov(2, _Tipo.SALIDA, 3),
            _mov(3, _Tipo.SALIDA, 2, herramienta=2),
            _mov(4, _Tipo.AJUSTE_NEGATIVO, 1, motivo="Rota"),
            _mov(5, _Tipo.TRANSFERENCIA_SALIDA, 5),
            _mov(6, _Tipo.SALIDA, 99, sucursal=2),  # otra sucursal: no entra
        ])
        totales = {t.tipo_movimiento: (t.movimientos, t.unidades) for t in cierre.totales}
        self.assertEqual(totales["ENTRADA"], (1, 24))
        self.assertEqual(totales["SALIDA"], (2, 5))
        self.assertEqual(totales["AJUSTE_NEGATIVO"], (1, 1))
        self.assertEqual(totales["TRANSFERENCIA_SALIDA"], (1, 5))
        self.assertEqual(totales["TRANSFERENCIA_ENTRADA"], (0, 0))
        self.assertEqual((cierre.cantidad_salidas, cierre.total_salidas_unidades), (2, 5))
        self.assertEqual([l.codigo for l in cierre.lineas], ["T-1", "T-1", "M-1", "T-1", "T-1"])
        self.assertEqual(cierre.sucursal_nombre, "Central")
        self.assertEqual(self.catalogo.llamadas, 1)  # una consulta al catálogo, no una por línea

    def test_dia_sin_movimientos(self):
        cierre = self._cierre([])
        self.assertEqual((cierre.lineas, cierre.cantidad_salidas, cierre.total_salidas_unidades), ((), 0, 0))
        self.assertEqual(self.catalogo.llamadas, 0)

    def test_permisos_por_rol_y_sucursal(self):
        self._cierre([], actor=_SUP_CENTRAL, sucursal_id=1)
        with self.assertRaises(ReporteNoPermitidoError):
            self._cierre([], actor=_SUP_CENTRAL, sucursal_id=2)
        with self.assertRaises(ReporteNoPermitidoError):
            self._cierre([], actor=_EMPLEADO, sucursal_id=1)
        self._cierre([], actor=_ADMIN, sucursal_id=2)

    def test_fecha_futura_y_sucursal_inexistente(self):
        with self.assertRaises(FechaFuturaError):
            self._cierre([], fecha=_date(2026, 10, 21))
        with self.assertRaises(SucursalInexistenteError):
            self._cierre([], sucursal_id=99)

    def test_dia_pasado(self):
        self._cierre([], fecha=_date(2026, 1, 15))
        self.assertEqual(self.repo.pedidos, [(1, _date(2026, 1, 15))])


class CierreDiarioApiTests(APITestCase):
    URL = "/api/indicadores/cierre-diario/"

    def setUp(self):
        from apps.catalogo.infrastructure.models import Herramienta as HerramientaModel
        from apps.movimientos.infrastructure.models import Movimiento
        from apps.usuarios.infrastructure.models import Sucursal as SucursalModel, Usuario

        self.Movimiento = Movimiento
        self.central = SucursalModel.objects.create(nombre="Central")
        self.norte = SucursalModel.objects.create(nombre="Norte")
        self.h = HerramientaModel.objects.create(codigo="T-1", nombre="Taladro", unidades_por_caja=12)
        self.admin = Usuario.objects.create_user("adm", password="x", rol="ADMINISTRADOR")
        self.sup = Usuario.objects.create_user("sup", password="x", rol="SUPERVISOR", sucursal=self.central)
        self.emp = Usuario.objects.create_user("emp", password="x", rol="EMPLEADO", sucursal=self.central)

    def _mov(self, tipo, unidades, cuando, sucursal=None):
        m = self.Movimiento.objects.create(
            herramienta=self.h, sucursal=sucursal or self.central, usuario=self.sup, tipo_movimiento=tipo,
            tipo_unidad="UNIDAD", cantidad=unidades, cantidad_unidades=unidades,
            motivo="x" if "AJUSTE" in tipo else "",
        )
        self.Movimiento.objects.filter(pk=m.pk).update(creado_en=cuando)

    def _la_paz(self, dia, hora, minuto=0):
        from django.utils import timezone
        return _datetime.combine(dia, _time(hora, minuto), tzinfo=timezone.get_current_timezone())

    def test_el_dia_es_el_de_la_paz(self):
        from django.utils import timezone
        ayer = timezone.localdate() - timedelta(days=1)
        # 23:30 de ayer en La Paz = 03:30 de hoy en UTC: es de AYER.
        self._mov("SALIDA", 2, self._la_paz(ayer, 23, 30))
        # 00:10 de hoy en La Paz = 04:10 UTC de hoy: es de HOY.
        self._mov("SALIDA", 5, self._la_paz(ayer + timedelta(days=1), 0, 10))
        self.client.force_authenticate(self.sup)
        de_ayer = self.client.get(self.URL, {"fecha": ayer.isoformat()}).json()
        self.assertEqual((de_ayer["cantidad_salidas"], de_ayer["total_salidas_unidades"]), (1, 2))
        de_hoy = self.client.get(self.URL).json()  # sin fecha = hoy
        self.assertEqual((de_hoy["cantidad_salidas"], de_hoy["total_salidas_unidades"]), (1, 5))
        self.assertTrue(de_ayer["lineas"][0]["fecha_hora"].endswith("-04:00"))

    def test_lineas_y_totales(self):
        from django.utils import timezone
        hoy = timezone.localdate()
        self._mov("ENTRADA", 24, self._la_paz(hoy, 0, 5))
        self._mov("SALIDA", 3, self._la_paz(hoy, 0, 20))
        self._mov("AJUSTE_NEGATIVO", 1, self._la_paz(hoy, 0, 30))
        self._mov("SALIDA", 7, self._la_paz(hoy, 0, 40), sucursal=self.norte)
        self.client.force_authenticate(self.admin)
        datos = self.client.get(self.URL, {"sucursal": self.central.id}).json()
        self.assertEqual([l["tipo_movimiento"] for l in datos["lineas"]], ["ENTRADA", "SALIDA", "AJUSTE_NEGATIVO"])
        self.assertEqual(datos["lineas"][0]["codigo"], "T-1")
        self.assertEqual(datos["lineas"][0]["usuario"], "sup")
        self.assertEqual(len(datos["totales"]), 6)
        self.assertEqual((datos["sucursal_nombre"], datos["total_salidas_unidades"]), ("Central", 3))

    def test_dia_sin_movimientos_responde_vacio(self):
        self.client.force_authenticate(self.sup)
        datos = self.client.get(self.URL).json()
        self.assertEqual((datos["lineas"], datos["cantidad_salidas"]), ([], 0))

    def test_permisos(self):
        self.client.force_authenticate(self.emp)
        self.assertEqual(self.client.get(self.URL).status_code, 403)
        self.client.force_authenticate(self.sup)
        self.assertEqual(self.client.get(self.URL, {"sucursal": self.norte.id}).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(self.URL, {"sucursal": self.norte.id}).status_code, 200)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.URL).status_code, 401)

    def test_validaciones(self):
        from django.utils import timezone
        self.client.force_authenticate(self.admin)
        sin_sucursal = self.client.get(self.URL)
        self.assertEqual(sin_sucursal.status_code, 400)
        self.assertIn("sucursal", sin_sucursal.json())
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        futura = self.client.get(self.URL, {"sucursal": self.central.id, "fecha": manana})
        self.assertEqual(futura.status_code, 400)
        self.assertIn("fecha", futura.json())
        self.assertEqual(self.client.get(self.URL, {"sucursal": self.central.id, "fecha": "20-10-2026"}).status_code, 400)
        self.assertEqual(self.client.get(self.URL, {"sucursal": 9999}).status_code, 400)

    def test_consultas_constantes(self):
        from django.utils import timezone
        hoy = timezone.localdate()
        for minuto in range(5):
            self._mov("SALIDA", 1, self._la_paz(hoy, 0, minuto))
        self.client.force_authenticate(self.sup)
        # sucursal + movimientos del día (con usuario) + catálogo
        with self.assertNumQueries(3):
            self.client.get(self.URL)


# --- Actualizar la demanda anual con la observada (HU21) ---

from dataclasses import replace as _replace

from apps.catalogo.domain.exceptions import HerramientaNoEncontradaError as _NoEncontrada

from .domain.exceptions import ActualizacionNoPermitidaError, SinVentasObservadasError
from .use_cases.actualizar_demanda import actualizar_demanda_anual


class _CatalogoEditable:
    def __init__(self, *herramientas):
        self.datos = {h.id: h for h in herramientas}
        self.guardadas = []

    def obtener_por_id(self, herramienta_id):
        return self.datos.get(herramienta_id)

    def guardar(self, h, imagen=None):
        self.guardadas.append(h)
        self.datos[h.id] = h
        return h


class _Ventas:
    def __init__(self, por_herramienta):
        self.por_herramienta = por_herramienta
        self.desde = None

    def unidades_por_herramienta(self, tipos, desde):
        self.tipos, self.desde = set(tipos), desde
        return self.por_herramienta


AHORA = _datetime(2026, 10, 27, 12, tzinfo=dt_timezone.utc)
ADMIN = _Actor(usuario_id=1, rol=_Rol.ADMINISTRADOR, sucursal_id=None)
SUPERVISOR = _Actor(usuario_id=2, rol=_Rol.SUPERVISOR, sucursal_id=1)
EMPLEADO = _Actor(usuario_id=3, rol=_Rol.EMPLEADO, sucursal_id=1)


class ActualizarDemandaUseCaseTests(SimpleTestCase):
    def _herramienta(self):
        return herramienta(1, demanda=100, entrega=10, costo_pedido=50, costo_alm=2, caja=12)

    def test_reemplaza_la_demanda_y_recalcula_el_eoq(self):
        catalogo, ventas = _CatalogoEditable(self._herramienta()), _Ventas({1: 1000})
        r = actualizar_demanda_anual(catalogo, ventas, ADMIN, 1, AHORA)
        self.assertEqual(catalogo.datos[1].demanda_anual, 1000)
        # raiz(2 * 1000 * 50 / 2) = 223.61 -> 228 en cajas de 12
        self.assertEqual((r.demanda_anual, r.demanda_observada, r.eoq, r.eoq_ajustado_cajas), (1000, 1000, 223.61, 228))

    def test_usa_las_ventas_de_los_ultimos_12_meses(self):
        ventas = _Ventas({1: 10})
        actualizar_demanda_anual(_CatalogoEditable(self._herramienta()), ventas, SUPERVISOR, 1, AHORA)
        self.assertEqual(ventas.desde, AHORA - timedelta(days=365))
        self.assertEqual(ventas.tipos, {T.SALIDA})

    def test_sin_ventas_no_actualiza(self):
        catalogo = _CatalogoEditable(self._herramienta())
        with self.assertRaises(SinVentasObservadasError):
            actualizar_demanda_anual(catalogo, _Ventas({}), ADMIN, 1, AHORA)
        self.assertEqual(catalogo.guardadas, [])

    def test_si_ya_coincide_no_guarda(self):
        catalogo = _CatalogoEditable(self._herramienta())
        actualizar_demanda_anual(catalogo, _Ventas({1: 100}), ADMIN, 1, AHORA)
        self.assertEqual(catalogo.guardadas, [])

    def test_empleado_no_puede(self):
        catalogo = _CatalogoEditable(self._herramienta())
        with self.assertRaises(ActualizacionNoPermitidaError):
            actualizar_demanda_anual(catalogo, _Ventas({1: 10}), EMPLEADO, 1, AHORA)
        self.assertEqual(catalogo.guardadas, [])

    def test_herramienta_inexistente(self):
        with self.assertRaises(_NoEncontrada):
            actualizar_demanda_anual(_CatalogoEditable(), _Ventas({}), ADMIN, 9, AHORA)


class ActualizarDemandaApiTests(APITestCase):
    """Mismos datos que IndicadoresApiTests (Taladro con D = 730)."""

    _mov = IndicadoresApiTests._mov

    def setUp(self):
        IndicadoresApiTests.setUp(self)
        from apps.usuarios.infrastructure.models import Usuario
        self.admin = Usuario.objects.create_user("adm", password="x", rol="ADMINISTRADOR")
        self.sup = Usuario.objects.create_user("sup", password="x", rol="SUPERVISOR", sucursal=self.central)

    def _url(self, h):
        return f"/api/indicadores/eoq/{h}/actualizar-demanda/"

    def test_supervisor_actualiza_y_el_rop_usa_la_nueva_demanda(self):
        self._mov(self.tal, "ENTRADA", 500, dias_atras=200)
        self._mov(self.tal, "SALIDA", 365, dias_atras=20)
        self._mov(self.tal, "AJUSTE_NEGATIVO", 50, dias_atras=5)  # no es venta
        self.client.force_authenticate(self.sup)
        respuesta = self.client.post(self._url(self.tal.id))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["demanda_anual"], 365)
        self.tal.refresh_from_db()
        self.assertEqual(self.tal.demanda_anual, 365)
        # ROP = 365 / 365 * 15 días = 15
        self.assertEqual(self.client.get(f"/api/indicadores/rop/{self.tal.id}/").json()["punto_reorden"], 15.0)

    def test_queda_en_el_historial_de_modificaciones(self):
        from apps.auditoria.infrastructure.models import HistorialModificacion
        self._mov(self.tal, "ENTRADA", 50, dias_atras=30)
        self._mov(self.tal, "SALIDA", 20, dias_atras=3)
        self.client.force_authenticate(self.admin)
        self.client.post(self._url(self.tal.id))
        ultimo = HistorialModificacion.objects.filter(accion="UPDATE").latest("id")
        self.assertEqual(ultimo.datos_nuevos["demanda_anual"], 20)

    def test_permisos_y_errores(self):
        self._mov(self.tal, "ENTRADA", 50, dias_atras=30)
        self._mov(self.tal, "SALIDA", 20, dias_atras=3)
        self.client.force_authenticate(self.u)  # Empleado
        self.assertEqual(self.client.post(self._url(self.tal.id)).status_code, 403)
        self.client.force_authenticate(self.admin)
        sin_ventas = self.client.post(self._url(self.amo.id))
        self.assertEqual(sin_ventas.status_code, 409)
        self.assertIn("detail", sin_ventas.json())
        self.assertEqual(self.client.post(self._url(999)).status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self._url(self.tal.id)).status_code, 401)


# --- Reporte de antigüedad (HU22) ---

from decimal import Decimal

from .domain.antiguedad import dias_sin_venta, tramo
from .use_cases.reporte_antiguedad import construir_reporte_antiguedad


class _SucursalesConId(_Repo):
    def obtener_por_id(self, sucursal_id):
        return next((s for s in self.datos if s.id == sucursal_id), None)


class AntiguedadDominioTests(SimpleTestCase):
    def test_tramos_con_corte_en_40_dias(self):
        self.assertEqual(
            [tramo(d) for d in (0, 30, 31, 40, 41, 90, 91, 500)],
            ["0–30 días", "0–30 días", "31–40 días", "31–40 días", "41–90 días", "41–90 días",
             "Más de 90 días", "Más de 90 días"],
        )

    def test_dias_desde_la_ultima_venta_o_el_primer_movimiento(self):
        self.assertEqual(dias_sin_venta(hace(5), hace(100), HOY), 5)
        self.assertEqual(dias_sin_venta(None, hace(100), HOY), 100)


class ReporteAntiguedadUseCaseTests(SimpleTestCase):
    sucursales = _SucursalesConId([Sucursal(1, "Central", ""), Sucursal(2, "Norte", "")])

    def setUp(self):
        con_costo = _replace(herramienta(1), costo_unitario=Decimal("12.50"))
        self.catalogo = _Repo([con_costo, herramienta(2), herramienta(3)])
        self.filas = _Repo([
            resumen(1, 1, entradas=10, salidas=2, ultima_salida=60),   # estancada, con costo
            resumen(1, 2, entradas=5, ultima_salida=None, primero=10),  # nunca vendida, reciente
            resumen(2, 1, entradas=4, salidas=1, ultima_salida=35),
            resumen(3, 1, entradas=3, salidas=3, ultima_salida=200),   # sin stock: no aparece
            resumen(2, 2, entradas=7, salidas=1, ultima_salida=95),    # estancada, sin costo
        ])

    def _reporte(self, actor, sucursal=None, dias_minimos=0):
        return construir_reporte_antiguedad(self.filas, self.catalogo, self.sucursales, actor, sucursal,
                                            hoy=HOY, dias_minimos=dias_minimos)

    def test_admin_ve_todas_las_sucursales_ordenadas_por_dias(self):
        r = self._reporte(ADMIN)
        self.assertEqual(
            [(l.herramienta_id, l.sucursal_nombre, l.stock, l.dias_sin_venta, l.estancada) for l in r.lineas],
            [(2, "Norte", 6, 95, True), (1, "Central", 8, 60, True), (2, "Central", 3, 35, False),
             (1, "Norte", 5, 10, False)],
        )
        self.assertEqual((r.total_unidades, r.total_estancadas, r.lineas_sin_costo), (22, 2, 2))
        # Solo la estancada con costo: 8 x 12.50 (la de Norte no tiene costo).
        self.assertEqual(r.valor_inmovilizado_estancado, Decimal("100.00"))
        self.assertEqual([(t.tramo, t.lineas, t.unidades) for t in r.tramos],
                         [("0–30 días", 1, 5), ("31–40 días", 1, 3), ("41–90 días", 1, 8), ("Más de 90 días", 1, 6)])
        self.assertTrue(r.lineas[3].nunca_vendida)

    def test_filtro_por_sucursal_y_dias_minimos(self):
        r = self._reporte(ADMIN, sucursal=1, dias_minimos=41)
        self.assertEqual([(l.herramienta_id, l.sucursal_id) for l in r.lineas], [(1, 1)])
        self.assertEqual(r.sucursal_id, 1)

    def test_supervisor_ve_solo_la_suya(self):
        r = self._reporte(SUPERVISOR)
        self.assertEqual({l.sucursal_id for l in r.lineas}, {1})
        self.assertEqual(r.sucursal_id, 1)
        with self.assertRaises(ReporteNoPermitidoError):
            self._reporte(SUPERVISOR, sucursal=2)

    def test_empleado_no_ve_el_reporte(self):
        with self.assertRaises(ReporteNoPermitidoError):
            self._reporte(EMPLEADO, sucursal=1)

    def test_sucursal_inexistente(self):
        with self.assertRaises(SucursalInexistenteError):
            self._reporte(ADMIN, sucursal=9)

    def test_el_panel_cuenta_las_mismas_estancadas(self):
        panel = construir_panel(self.filas, self.catalogo, self.sucursales, hoy=HOY)
        reporte = self._reporte(ADMIN)
        self.assertEqual(
            {(e.herramienta_id, e.sucursal_id, e.dias_sin_venta) for e in panel.estancadas},
            {(l.herramienta_id, l.sucursal_id, l.dias_sin_venta) for l in reporte.lineas if l.estancada},
        )


class ReporteAntiguedadApiTests(APITestCase):
    URL = "/api/indicadores/antiguedad/"

    def setUp(self):
        CierreDiarioApiTests.setUp(self)
        self.h.costo_unitario = Decimal("10")
        self.h.save()
        from django.utils import timezone
        ahora = timezone.now()
        self._mov("ENTRADA", 20, ahora - timedelta(days=80))
        self._mov("SALIDA", 5, ahora - timedelta(days=50))
        self._mov("ENTRADA", 4, ahora - timedelta(days=3), sucursal=self.norte)

    _mov = CierreDiarioApiTests._mov

    def test_admin_todas_y_filtradas(self):
        self.client.force_authenticate(self.admin)
        datos = self.client.get(self.URL).json()
        self.assertEqual([(l["sucursal_nombre"], l["stock"], l["estancada"]) for l in datos["lineas"]],
                         [("Central", 15, True), ("Norte", 4, False)])
        self.assertEqual((datos["sucursal_id"], datos["valor_inmovilizado_estancado"]), (None, "150.00"))
        filtrado = self.client.get(self.URL, {"sucursal": self.norte.id}).json()
        self.assertEqual([l["sucursal_nombre"] for l in filtrado["lineas"]], ["Norte"])
        self.assertEqual(len(self.client.get(self.URL, {"dias_minimos": 41}).json()["lineas"]), 1)

    def test_permisos_por_rol(self):
        self.client.force_authenticate(self.sup)
        self.assertEqual([l["sucursal_nombre"] for l in self.client.get(self.URL).json()["lineas"]], ["Central"])
        self.assertEqual(self.client.get(self.URL, {"sucursal": self.norte.id}).status_code, 403)
        self.client.force_authenticate(self.emp)
        self.assertEqual(self.client.get(self.URL).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.URL).status_code, 401)

    def test_validaciones(self):
        self.client.force_authenticate(self.admin)
        self.assertIn("sucursal", self.client.get(self.URL, {"sucursal": 999}).json())
        self.assertIn("dias_minimos", self.client.get(self.URL, {"dias_minimos": -1}).json())
