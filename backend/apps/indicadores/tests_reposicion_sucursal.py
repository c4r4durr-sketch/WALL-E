"""
Pruebas del EOQ y el ROP por sucursal y del dashboard "Productos para
pedir" (use_cases/reposicion_por_sucursal.py).

Correr con: python manage.py test apps.indicadores
"""

from datetime import datetime, timedelta, timezone as dt_timezone

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.catalogo.domain.entities import Herramienta
from apps.movimientos.domain.entities import ResumenInventario
from apps.movimientos.domain.value_objects import TipoMovimiento as T
from apps.usuarios.domain.entities import Sucursal

from .domain.exceptions import SucursalInexistenteError
from .domain.formulas import DEMANDA_ESTIMADA, DEMANDA_OBSERVADA, demanda_de_sucursal
from .use_cases.reposicion_por_sucursal import eoq_por_sucursal, productos_para_pedir

AHORA = datetime(2026, 11, 20, 12, tzinfo=dt_timezone.utc)


class DemandaDeSucursalTests(SimpleTestCase):
    def test_con_ventas_en_la_sucursal_usa_sus_ventas(self):
        self.assertEqual(demanda_de_sucursal(730, 40, 100, 2), (40, DEMANDA_OBSERVADA))

    def test_vendida_solo_en_otras_sucursales_es_cero(self):
        self.assertEqual(demanda_de_sucursal(730, 0, 100, 2), (0, DEMANDA_OBSERVADA))

    def test_sin_ventas_en_ninguna_reparte_la_estimada_hacia_arriba(self):
        self.assertEqual(demanda_de_sucursal(731, 0, 0, 2), (366, DEMANDA_ESTIMADA))
        self.assertEqual(demanda_de_sucursal(None, 0, 0, 2), (None, DEMANDA_ESTIMADA))


class _Repo:
    def __init__(self, datos, vendidas=None):
        self.datos = datos
        self.vendidas = vendidas or {}

    def listar(self):
        return self.datos

    def obtener_por_id(self, id):
        return next((h for h in self.datos if h.id == id), None)

    def resumen_inventario(self):
        return self.datos

    def unidades_por_herramienta_y_sucursal(self, tipos, desde):
        return self.vendidas


def herramienta(id, demanda=730, entrega=10, costo_pedido=50, costo_alm=2, caja=12):
    return Herramienta(id=id, codigo=f"H-{id}", nombre=f"Herramienta {id}", modelo="",
                       unidades_por_caja=caja, demanda_anual=demanda, tiempo_entrega_dias=entrega,
                       costo_pedido=costo_pedido, costo_almacenamiento_unitario=costo_alm)


def stock(h, s, entradas=0, salidas=0):
    return ResumenInventario(h, s, {T.ENTRADA: entradas, T.SALIDA: salidas}, AHORA, None)


SUCURSALES = _Repo([Sucursal(1, "Central", ""), Sucursal(2, "Norte", ""), Sucursal(3, "Cerrada", "", activa=False)])


class ProductosParaPedirTests(SimpleTestCase):
    def _pedir(self, herramientas, filas, vendidas, sucursal_id=None):
        return productos_para_pedir(_Repo(herramientas), _Repo(filas, vendidas), SUCURSALES,
                                    ahora=AHORA, sucursal_id=sucursal_id)

    def test_cada_sucursal_con_su_demanda_y_su_stock(self):
        # Central vendió 365 -> ROP 10, stock 8 -> pedir; EOQ raiz(2*365*50/2) = 135.1 -> 144 (12 cajas).
        # Norte vendió 73 -> ROP 2, stock 8 -> no.
        r = self._pedir([herramienta(1)], [stock(1, 1, entradas=8), stock(1, 2, entradas=8)],
                        {(1, 1): 365, (1, 2): 73})
        self.assertEqual((r.total_lineas, r.total_herramientas), (1, 1))
        linea = r.lineas[0]
        self.assertEqual((linea.sucursal_nombre, linea.stock, linea.punto_reorden, linea.eoq_ajustado_cajas),
                         ("Central", 8, 10.0, 144))

    def test_una_entrada_saca_la_linea_pero_no_cambia_el_eoq(self):
        antes = self._pedir([herramienta(1)], [stock(1, 1, entradas=8)], {(1, 1): 365}).lineas[0]
        despues = self._pedir([herramienta(1)], [stock(1, 1, entradas=208)], {(1, 1): 365})
        self.assertEqual(despues.total_lineas, 0)
        from .use_cases.reposicion_por_sucursal import linea_sucursal
        linea = linea_sucursal(herramienta(1), Sucursal(1, "Central", ""), 208, 365, 365, 2)
        self.assertEqual(linea.eoq, antes.eoq)
        self.assertFalse(linea.requiere_reorden)

    def test_sin_demanda_en_la_sucursal_no_se_pide_aunque_no_tenga_stock(self):
        # Se vende solo en Central: Norte (stock 0, D = 0) no aparece.
        r = self._pedir([herramienta(1)], [stock(1, 1, entradas=500)], {(1, 1): 365})
        self.assertEqual(r.total_lineas, 0)

    def test_herramienta_nueva_usa_la_estimada_repartida_entre_las_activas(self):
        # Sin ventas: 730 / 2 sucursales activas = 365 cada una -> ROP 10 en las dos.
        r = self._pedir([herramienta(1)], [], {})
        self.assertEqual([(l.sucursal_id, l.punto_reorden, l.fuente_demanda) for l in r.lineas],
                         [(1, 10.0, DEMANDA_ESTIMADA), (2, 10.0, DEMANDA_ESTIMADA)])

    def test_sin_datos_se_cuenta_y_no_aparece(self):
        r = self._pedir([herramienta(1, entrega=None), herramienta(2, demanda=None)], [], {})
        self.assertEqual((r.total_lineas, r.herramientas_sin_datos), (0, 2))

    def test_filtro_por_sucursal_y_sucursal_inactiva(self):
        r = self._pedir([herramienta(1)], [], {}, sucursal_id=2)
        self.assertEqual([l.sucursal_id for l in r.lineas], [2])
        with self.assertRaises(SucursalInexistenteError):
            self._pedir([herramienta(1)], [], {}, sucursal_id=3)

    def test_lo_mas_urgente_primero(self):
        r = self._pedir([herramienta(1), herramienta(2)],
                        [stock(1, 1, entradas=9), stock(2, 1, entradas=1)],
                        {(1, 1): 365, (2, 1): 365})
        self.assertEqual([l.herramienta_id for l in r.lineas], [2, 1])


class EOQPorSucursalTests(SimpleTestCase):
    def test_general_suma_las_sucursales_y_el_detalle_las_separa(self):
        r = eoq_por_sucursal(_Repo([herramienta(1)]),
                             _Repo([stock(1, 1, entradas=8), stock(1, 2, entradas=4)], {(1, 1): 365, (1, 2): 365}),
                             SUCURSALES, 1, ahora=AHORA)
        # General: D = 730 -> ROP 20 con stock 12; cada sucursal D = 365 -> ROP 10.
        self.assertEqual((r.general_eoq.demanda_usada, r.general_rop.punto_reorden, r.general_rop.stock_total),
                         (730, 20.0, 12))
        self.assertEqual([(s.sucursal_id, s.demanda_usada, s.punto_reorden, s.stock) for s in r.sucursales],
                         [(1, 365, 10.0, 8), (2, 365, 10.0, 4)])


class ReposicionSucursalApiTests(APITestCase):
    def setUp(self):
        from apps.catalogo.infrastructure.models import Herramienta as HerramientaModel
        from apps.movimientos.infrastructure.models import Movimiento
        from apps.usuarios.infrastructure.models import Sucursal as SucursalModel, Usuario

        self.Movimiento = Movimiento
        self.central = SucursalModel.objects.create(nombre="Central")
        self.norte = SucursalModel.objects.create(nombre="Norte")
        self.u = Usuario.objects.create_user("emp", password="x", rol="EMPLEADO", sucursal=self.central)
        self.tal = HerramientaModel.objects.create(codigo="TAL", nombre="Taladro", unidades_por_caja=6,
                                                   demanda_anual=730, tiempo_entrega_dias=10,
                                                   costo_pedido=120, costo_almacenamiento_unitario=8)
        self.client.force_authenticate(self.u)

    def _mov(self, tipo, n, sucursal, dias_atras=0):
        from django.utils import timezone
        m = self.Movimiento.objects.create(herramienta=self.tal, sucursal=sucursal, usuario=self.u,
                                           tipo_movimiento=tipo, tipo_unidad="UNIDAD", cantidad=n,
                                           cantidad_unidades=n)
        self.Movimiento.objects.filter(pk=m.pk).update(creado_en=timezone.now() - timedelta(days=dias_atras))

    def test_productos_para_pedir_y_eoq_por_sucursal(self):
        self._mov("ENTRADA", 400, self.central, dias_atras=200)
        self._mov("SALIDA", 365, self.central, dias_atras=30)   # Central: D 365, ROP 10, stock 35
        self._mov("ENTRADA", 50, self.norte, dias_atras=200)
        self._mov("SALIDA", 45, self.norte, dias_atras=30)      # Norte: D 45, ROP 1.23, stock 5
        self._mov("SALIDA", 30, self.central, dias_atras=500)   # fuera del período: no es demanda
        # Central: stock 400 - 365 - 30 = 5 <= ROP 10 -> pedir. Norte: 5 > 1.23 -> no.
        datos = self.client.get("/api/indicadores/productos-para-pedir/").json()
        self.assertEqual(datos["total_lineas"], 1)
        linea = datos["lineas"][0]
        # EOQ = raiz(2*365*120/8) = 104.64 -> 108 en cajas de 6.
        self.assertEqual((linea["sucursal_id"], linea["stock"], linea["punto_reorden"], linea["eoq_ajustado_cajas"]),
                         (self.central.id, 5, 10.0, 108))

        # Una entrada en Central lo saca de la lista; el EOQ sigue igual.
        self._mov("ENTRADA", 100, self.central)
        self.assertEqual(self.client.get("/api/indicadores/productos-para-pedir/").json()["total_lineas"], 0)
        detalle = self.client.get(f"/api/indicadores/eoq/{self.tal.id}/sucursales/").json()
        central = next(s for s in detalle["sucursales"] if s["sucursal_id"] == self.central.id)
        self.assertEqual((central["eoq"], central["stock"], central["requiere_reorden"]), (104.64, 105, False))
        self.assertEqual(detalle["general_eoq"]["demanda_usada"], 410)

    def test_filtro_de_sucursal(self):
        self.assertEqual(self.client.get("/api/indicadores/productos-para-pedir/",
                                         {"sucursal": self.norte.id}).status_code, 200)
        self.assertEqual(self.client.get("/api/indicadores/productos-para-pedir/",
                                         {"sucursal": 9999}).status_code, 400)

    def test_herramienta_inexistente_es_404_y_sin_sesion_401(self):
        self.assertEqual(self.client.get("/api/indicadores/eoq/9999/sucursales/").status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/indicadores/productos-para-pedir/").status_code, 401)
