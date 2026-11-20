"""
Pruebas de los reportes estadísticos (/api/indicadores/estadisticas/...).

Las reglas puras (periodo, meses, Pareto) van con SimpleTestCase; los
endpoints, con datos conocidos en la base de pruebas. Las fechas se fijan
en días antes de hoy (al mediodía de La Paz), así las pruebas dan lo mismo
cualquier día que se corran.

Correr con: python manage.py test apps.indicadores
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import BytesIO

from django.test import SimpleTestCase
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.test import APITestCase

from .domain.estadisticas import (
    VentaHerramienta,
    clasificar_por_valor,
    errores_de_periodo,
    meses_del_rango,
    periodo_por_defecto,
)


class PeriodoTests(SimpleTestCase):
    def test_por_defecto_son_los_ultimos_12_meses_calendario(self):
        self.assertEqual(periodo_por_defecto(date(2026, 11, 19)), (date(2025, 12, 1), date(2026, 11, 19)))
        self.assertEqual(periodo_por_defecto(date(2026, 1, 5)), (date(2025, 2, 1), date(2026, 1, 5)))
        self.assertEqual(periodo_por_defecto(date(2026, 12, 31)), (date(2026, 1, 1), date(2026, 12, 31)))

    def test_fechas_futuras_y_hasta_antes_de_desde(self):
        hoy = date(2026, 11, 19)
        self.assertEqual(errores_de_periodo(date(2026, 1, 1), hoy, hoy), {})
        self.assertEqual(errores_de_periodo(hoy, hoy, hoy), {})
        self.assertEqual(set(errores_de_periodo(date(2026, 11, 20), date(2026, 11, 21), hoy)), {"desde", "hasta"})
        self.assertIn("Hasta", errores_de_periodo(date(2026, 5, 2), date(2026, 5, 1), hoy)["hasta"])

    def test_meses_del_rango_cruzando_el_anio(self):
        self.assertEqual(
            meses_del_rango(date(2025, 11, 15), date(2026, 2, 1)),
            [date(2025, 11, 1), date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)],
        )
        self.assertEqual(meses_del_rango(date(2026, 3, 9), date(2026, 3, 9)), [date(2026, 3, 1)])


def _venta(id, monto, unidades=1):
    return VentaHerramienta(id, f"H-{id}", f"Herramienta {id}", unidades, None if monto is None else Decimal(monto))


class ParetoPorValorTests(SimpleTestCase):
    def test_clasifica_por_el_acumulado_anterior(self):
        # 70 / 20 / 6 / 4 de 100: A (0 %), B (70 %)... la segunda empieza en
        # 70 < 80 -> A; la tercera en 90 -> B; la cuarta en 96 -> C.
        clases, pareto, total = clasificar_por_valor(
            [_venta(1, "70"), _venta(2, "20"), _venta(3, "6"), _venta(4, "4")], sin_ventas=0
        )
        self.assertEqual(total, Decimal("100"))
        self.assertEqual([(p.codigo, p.clase, p.porcentaje_acumulado) for p in pareto],
                         [("H-1", "A", 70.0), ("H-2", "A", 90.0), ("H-3", "B", 96.0), ("H-4", "C", 100.0)])
        self.assertEqual([(c.clase, c.herramientas, c.porcentaje_valor) for c in clases],
                         [("A", 2, 90.0), ("B", 1, 6.0), ("C", 1, 4.0)])

    def test_la_mayor_es_a_aunque_supere_el_80(self):
        # La segunda empieza en 95 %, que ya no es < 95: C.
        _, pareto, _ = clasificar_por_valor([_venta(2, "5"), _venta(1, "95")], sin_ventas=0)
        self.assertEqual([(p.codigo, p.clase) for p in pareto], [("H-1", "A"), ("H-2", "C")])

    def test_sin_ventas_suman_a_c_y_sin_costo_quedan_fuera(self):
        clases, pareto, _ = clasificar_por_valor([_venta(1, "10"), _venta(2, None)], sin_ventas=3)
        self.assertEqual([p.codigo for p in pareto], ["H-1"])
        self.assertEqual([(c.clase, c.herramientas) for c in clases], [("A", 1), ("B", 0), ("C", 3)])

    def test_sin_valor_es_vacio(self):
        self.assertEqual(clasificar_por_valor([_venta(1, None)], sin_ventas=2), ((), (), Decimal("0")))


def _mes(dia: date) -> str:
    return f"{dia:%Y-%m}"


class EstadisticasApiTests(APITestCase):
    """Datos (A = hace 75 días, B = hace 20):
    Central: T-1 (costo 10) entra 100 en A, vende 30 en A y 20 en B, ajuste
             −5 en B; T-2 (costo 5) entra 50 y vende 10 en B; T-3 (sin
             costo) entra 8 y vende 2 en B; T-4 (costo 2) entra 10 hace 120
             días y nunca se vende.
    Norte:   T-1 entra 40 en A y nunca se vende.
    Sur:     sin movimientos."""

    BASE = "/api/indicadores/estadisticas/"

    def setUp(self):
        from apps.catalogo.infrastructure.models import Herramienta
        from apps.movimientos.infrastructure.models import Movimiento
        from apps.transferencias.infrastructure.models import Transferencia
        from apps.usuarios.infrastructure.models import Sucursal, Usuario

        self.Movimiento = Movimiento
        self.hoy = timezone.localdate()
        self.dia_a = self.hoy - timedelta(days=75)
        self.dia_b = self.hoy - timedelta(days=20)
        self.desde = self.hoy - timedelta(days=100)

        self.central = Sucursal.objects.create(nombre="Central")
        self.norte = Sucursal.objects.create(nombre="Norte")
        self.sur = Sucursal.objects.create(nombre="Sur")
        self.admin = Usuario.objects.create_user("adm", password="x", rol="ADMINISTRADOR")
        self.sup = Usuario.objects.create_user("sup", password="x", rol="SUPERVISOR", sucursal=self.central)
        self.emp = Usuario.objects.create_user("emp", password="x", rol="EMPLEADO", sucursal=self.central)

        h1 = Herramienta.objects.create(codigo="T-1", nombre="Taladro", costo_unitario=Decimal("10"))
        h2 = Herramienta.objects.create(codigo="T-2", nombre="Sierra", costo_unitario=Decimal("5"))
        h3 = Herramienta.objects.create(codigo="T-3", nombre="Lija")
        h4 = Herramienta.objects.create(codigo="T-4", nombre="Clavos", costo_unitario=Decimal("2"))

        for h, sucursal, tipo, n, dia in [
            (h1, self.central, "ENTRADA", 100, self.dia_a),
            (h1, self.central, "SALIDA", 30, self.dia_a),
            (h1, self.central, "SALIDA", 20, self.dia_b),
            (h1, self.central, "AJUSTE_NEGATIVO", 5, self.dia_b),
            (h2, self.central, "ENTRADA", 50, self.dia_b),
            (h2, self.central, "SALIDA", 10, self.dia_b),
            (h3, self.central, "ENTRADA", 8, self.dia_b),
            (h3, self.central, "SALIDA", 2, self.dia_b),
            (h4, self.central, "ENTRADA", 10, self.hoy - timedelta(days=120)),
            (h1, self.norte, "ENTRADA", 40, self.dia_a),
        ]:
            m = Movimiento.objects.create(
                herramienta=h, sucursal=sucursal, usuario=self.sup, tipo_movimiento=tipo, tipo_unidad="UNIDAD",
                cantidad=n, cantidad_unidades=n, motivo="x" if "AJUSTE" in tipo else "",
            )
            Movimiento.objects.filter(pk=m.pk).update(creado_en=self._mediodia(dia))

        for origen, destino, estado, dia in [
            (self.norte, self.central, "PENDIENTE", self.dia_a),
            (self.central, self.norte, "COMPLETADA", self.dia_b),
            (self.central, self.norte, "COMPLETADA", self.dia_b),
            (self.central, self.norte, "RECHAZADA", self.dia_b),
            (self.sur, self.central, "RECHAZADA", self.dia_b),
        ]:
            t = Transferencia.objects.create(
                herramienta=h1, sucursal_origen=origen, sucursal_destino=destino, usuario=self.sup,
                cantidad=1, tipo_unidad="UNIDAD", cantidad_unidades=1, estado=estado,
            )
            Transferencia.objects.filter(pk=t.pk).update(creado_en=self._mediodia(dia))

    def _mediodia(self, dia: date) -> datetime:
        return datetime.combine(dia, time(12), tzinfo=timezone.get_current_timezone())

    def _get(self, reporte, usuario=None, **params):
        self.client.force_authenticate(usuario or self.admin)
        params.setdefault("desde", self.desde.isoformat())
        return self.client.get(f"{self.BASE}{reporte}/", {k: v for k, v in params.items() if v is not None})

    # --- Totales con datos conocidos ---

    def test_movimientos_por_mes(self):
        datos = self._get("movimientos-por-mes").json()
        meses = {m["mes"]: m for m in datos["meses"]}
        self.assertEqual(list(meses), [_mes(m) for m in meses_del_rango(self.desde, self.hoy)])
        self.assertEqual(datos["periodo"], {"desde": self.desde.isoformat(), "hasta": self.hoy.isoformat(),
                                            "sucursal_id": None})
        a, b = meses[_mes(self.dia_a)], meses[_mes(self.dia_b)]
        self.assertEqual((a["entradas"], a["salidas"]), (140, 30))
        self.assertEqual((b["entradas"], b["salidas"], b["ajustes_negativos"], b["ajustes_positivos"]), (58, 32, 5, 0))
        otros = [m for k, m in meses.items() if k not in (_mes(self.dia_a), _mes(self.dia_b))]
        self.assertTrue(all(m["entradas"] == m["salidas"] == 0 for m in otros))

    def test_top_herramientas(self):
        datos = self._get("top-herramientas").json()
        self.assertEqual([(h["codigo"], h["unidades"], h["monto"]) for h in datos["herramientas"]],
                         [("T-1", 50, "500.00"), ("T-2", 10, "50.00"), ("T-3", 2, None)])

    def test_stock_por_sucursal(self):
        datos = self._get("stock-por-sucursal").json()
        self.assertEqual([(s["nombre"], s["unidades"], s["valor"], s["unidades_sin_costo"]) for s in datos["sucursales"]],
                         [("Central", 101, "670.00", 6), ("Norte", 40, "400.00", 0)])
        self.assertEqual((datos["total_unidades"], datos["total_valor"]), (141, "1070.00"))

    def test_abc(self):
        datos = self._get("abc").json()
        self.assertEqual([(c["clase"], c["herramientas"], c["valor"], c["porcentaje_valor"]) for c in datos["clases"]],
                         [("A", 1, "500.00", 90.91), ("B", 1, "50.00", 9.09), ("C", 1, "0.00", 0.0)])
        self.assertEqual([(p["codigo"], p["clase"], p["porcentaje_acumulado"]) for p in datos["pareto"]],
                         [("T-1", "A", 90.91), ("T-2", "B", 100.0)])
        self.assertEqual((datos["valor_total"], datos["herramientas_sin_costo"]), ("550.00", 1))

    def test_antiguedad(self):
        datos = self._get("antiguedad").json()
        self.assertEqual([(t["tramo"], t["herramientas"], t["unidades"], t["valor"]) for t in datos["tramos"]], [
            ("0–30 días", 3, 91, "650.00"),
            ("31–40 días", 0, 0, "0.00"),
            ("41–90 días", 1, 40, "400.00"),
            ("Más de 90 días", 1, 10, "20.00"),
        ])
        self.assertEqual((datos["valor_total"], datos["lineas_sin_costo"]), ("1070.00", 1))

    def test_transferencias(self):
        datos = self._get("transferencias").json()
        self.assertEqual([(e["estado"], e["cantidad"]) for e in datos["por_estado"]],
                         [("PENDIENTE", 1), ("COMPLETADA", 2), ("RECHAZADA", 2)])
        self.assertEqual(datos["total"], 5)
        meses = {m["mes"]: m for m in datos["por_mes"]}
        self.assertEqual(meses[_mes(self.dia_a)]["pendientes"], 1)
        self.assertEqual((meses[_mes(self.dia_b)]["completadas"], meses[_mes(self.dia_b)]["rechazadas"]), (2, 2))

    def test_resumen(self):
        datos = self._get("resumen").json()
        self.assertEqual(
            {k: datos[k] for k in ("total_movimientos", "unidades_vendidas", "valor_inventario",
                                   "alertas_reorden", "herramientas_estancadas")},
            # Sin datos EOQ en el catálogo no hay punto de reorden: 0 alertas.
            {"total_movimientos": 9, "unidades_vendidas": 62, "valor_inventario": "1070.00",
             "alertas_reorden": 0, "herramientas_estancadas": 2},
        )

    # --- Filtros ---

    def test_filtro_por_sucursal(self):
        norte = {"sucursal": self.norte.id}
        self.assertEqual([s["nombre"] for s in self._get("stock-por-sucursal", **norte).json()["sucursales"]], ["Norte"])
        meses = {m["mes"]: m for m in self._get("movimientos-por-mes", **norte).json()["meses"]}
        self.assertEqual(meses[_mes(self.dia_a)]["entradas"], 40)
        self.assertEqual(self._get("top-herramientas", **norte).json()["herramientas"], [])
        self.assertEqual(self._get("transferencias", **norte).json()["total"], 4)
        self.assertEqual(self._get("resumen", **norte).json()["herramientas_estancadas"], 1)

    def test_filtro_hasta_es_la_foto_de_ese_dia(self):
        hasta = (self.hoy - timedelta(days=50)).isoformat()
        stock = self._get("stock-por-sucursal", hasta=hasta).json()
        self.assertEqual([(s["nombre"], s["unidades"]) for s in stock["sucursales"]], [("Central", 80), ("Norte", 40)])
        tramos = {t["tramo"]: t["unidades"] for t in self._get("antiguedad", hasta=hasta).json()["tramos"]}
        self.assertEqual((tramos["0–30 días"], tramos["41–90 días"], tramos["Más de 90 días"]), (110, 10, 0))
        top = self._get("top-herramientas", hasta=hasta).json()["herramientas"]
        self.assertEqual([(h["codigo"], h["unidades"]) for h in top], [("T-1", 30)])

    def test_filtro_desde_deja_afuera_lo_anterior(self):
        datos = self._get("resumen", desde=(self.hoy - timedelta(days=30)).isoformat()).json()
        self.assertEqual((datos["total_movimientos"], datos["unidades_vendidas"]), (6, 32))

    def test_sin_fechas_son_los_ultimos_12_meses(self):
        self.client.force_authenticate(self.admin)
        periodo = self.client.get(f"{self.BASE}resumen/").json()["periodo"]
        self.assertEqual((periodo["desde"], periodo["hasta"]),
                         tuple(d.isoformat() for d in periodo_por_defecto(self.hoy)))

    def test_validaciones(self):
        manana = (self.hoy + timedelta(days=1)).isoformat()
        self.assertIn("desde", self._get("resumen", desde=manana).json())
        self.assertIn("hasta", self._get("resumen", hasta=manana).json())
        ayer = (self.hoy - timedelta(days=1)).isoformat()
        respuesta = self._get("abc", desde=self.hoy.isoformat(), hasta=ayer)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("hasta", respuesta.json())
        self.assertIn("desde", self._get("abc", desde="19/11/2026").json())
        self.assertIn("sucursal", self._get("abc", sucursal=999).json())

    # --- Permisos ---

    REPORTES = ("resumen", "movimientos-por-mes", "top-herramientas", "stock-por-sucursal", "abc", "antiguedad",
                "transferencias", "excel")

    def test_empleado_recibe_403_en_todos(self):
        for reporte in self.REPORTES:
            with self.subTest(reporte):
                self.assertEqual(self._get(reporte, usuario=self.emp).status_code, 403)

    def test_sin_sesion_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"{self.BASE}resumen/").status_code, 401)

    def test_supervisor_solo_su_sucursal(self):
        stock = self._get("stock-por-sucursal", usuario=self.sup).json()
        self.assertEqual((stock["periodo"]["sucursal_id"], [s["nombre"] for s in stock["sucursales"]]),
                         (self.central.id, ["Central"]))
        meses = {m["mes"]: m for m in self._get("movimientos-por-mes", usuario=self.sup).json()["meses"]}
        self.assertEqual(meses[_mes(self.dia_a)]["entradas"], 100)
        self.assertEqual(self._get("abc", usuario=self.sup, sucursal=self.central.id).status_code, 200)
        for reporte in self.REPORTES:
            with self.subTest(reporte):
                self.assertEqual(self._get(reporte, usuario=self.sup, sucursal=self.norte.id).status_code, 403)

    # --- Periodo sin datos ---

    def test_periodo_sin_datos_responde_vacio(self):
        vacio = {"sucursal": self.sur.id}
        self.assertEqual(self._get("movimientos-por-mes", **vacio).json()["meses"], [])
        self.assertEqual(self._get("top-herramientas", **vacio).json()["herramientas"], [])
        stock = self._get("stock-por-sucursal", **vacio).json()
        self.assertEqual((stock["sucursales"], stock["total_valor"]), ([], "0.00"))
        abc = self._get("abc", **vacio).json()
        self.assertEqual((abc["clases"], abc["pareto"]), ([], []))
        self.assertEqual(self._get("antiguedad", **vacio).json()["tramos"], [])
        transferencias = self._get("transferencias", desde=self.hoy.isoformat()).json()
        self.assertEqual((transferencias["por_estado"], transferencias["por_mes"], transferencias["total"]), ([], [], 0))
        resumen = self._get("resumen", **vacio).json()
        self.assertEqual((resumen["total_movimientos"], resumen["unidades_vendidas"]), (0, 0))

    # --- Excel ---

    def test_excel_una_hoja_por_grafico(self):
        respuesta = self._get("excel")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("spreadsheetml", respuesta["Content-Type"])
        libro = load_workbook(BytesIO(respuesta.content))
        self.assertEqual(libro.sheetnames, ["Resumen", "Movimientos por mes", "Top 10 vendidas", "Stock por sucursal",
                                            "Clasificación ABC", "Antigüedad del stock", "Transferencias"])
        top = libro["Top 10 vendidas"]
        self.assertEqual([c.value for c in top[5]], ["T-1", "Taladro", 50, 500])

    def test_excel_vacio_409(self):
        # Sur no tiene movimientos, y hoy no hubo transferencias.
        respuesta = self._get("excel", sucursal=self.sur.id, desde=self.hoy.isoformat())
        self.assertEqual(respuesta.status_code, 409)
