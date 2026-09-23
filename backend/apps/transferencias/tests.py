"""
Pruebas de transferencias (HU12): solicitar, completar y rechazar, con
sus validaciones de stock, sucursales y permisos por rol.

Correr con: python manage.py test apps.transferencias
"""

from rest_framework.test import APITestCase

from apps.catalogo.infrastructure.models import Herramienta
from apps.movimientos.infrastructure.models import Movimiento
from apps.usuarios.infrastructure.models import Sucursal, Usuario

from .infrastructure.models import Transferencia

URL = "/api/transferencias/"


class TransferenciaApiTests(APITestCase):
    def setUp(self):
        self.central = Sucursal.objects.create(nombre="Central")
        self.norte = Sucursal.objects.create(nombre="Norte")
        self.cerrada = Sucursal.objects.create(nombre="Cerrada", activa=False)
        self.h = Herramienta.objects.create(codigo="T-1", nombre="Taladro", unidades_por_caja=12)
        self.admin = Usuario.objects.create_user("admin_t", password="x", rol="ADMINISTRADOR")
        self.sup = Usuario.objects.create_user("sup_t", password="x", rol="SUPERVISOR", sucursal=self.norte)
        self.emp = Usuario.objects.create_user("emp_t", password="x", rol="EMPLEADO", sucursal=self.central)
        # 30 unidades en Central.
        Movimiento.objects.create(herramienta=self.h, sucursal=self.central, usuario=self.admin,
                                  tipo_movimiento="ENTRADA", tipo_unidad="UNIDAD", cantidad=30, cantidad_unidades=30)
        self.client.force_authenticate(self.emp)

    def _solicitar(self, cantidad=2, unidad="CAJA", origen=None, destino=None):
        return self.client.post(URL, {
            "herramienta": self.h.id, "sucursal_origen": origen or self.central.id,
            "sucursal_destino": destino or self.norte.id, "tipo_unidad": unidad, "cantidad": cantidad,
        }, format="json")

    def _stock(self):
        filas = self.client.get("/api/movimientos/stock/", {"herramienta": self.h.id}).json()
        return {f["sucursal_nombre"]: f["unidades"] for f in filas}

    def _como(self, usuario):
        self.client.force_authenticate(usuario)

    # --- Solicitar ---

    def test_empleado_solicita_desde_su_sucursal_y_queda_pendiente_sin_mover_stock(self):
        respuesta = self._solicitar()
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertEqual((datos["estado"], datos["cantidad_unidades"], datos["usuario_username"]),
                         ("PENDIENTE", 24, "emp_t"))
        self._como(self.admin)
        self.assertEqual(self._stock(), {"Central": 30, "Norte": 0})

    def test_empleado_no_solicita_desde_otra_sucursal(self):
        self.assertEqual(self._solicitar(origen=self.norte.id, destino=self.central.id).status_code, 403)

    def test_validaciones_de_solicitud(self):
        self._como(self.admin)
        misma = self._solicitar(destino=self.central.id)
        self.assertEqual(misma.status_code, 400)
        self.assertIn("sucursal_destino", misma.json())
        self.assertEqual(self._solicitar(destino=self.cerrada.id).status_code, 400)
        sin_stock = self._solicitar(cantidad=3)  # 36 > 30
        self.assertEqual(sin_stock.status_code, 400)
        self.assertIn("Stock insuficiente en origen", sin_stock.json()["cantidad"][0])
        self.assertEqual(Transferencia.objects.count(), 0)

    # --- Completar ---

    def test_completar_mueve_el_stock_y_genera_dos_movimientos(self):
        transferencia_id = self._solicitar().json()["id"]
        self._como(self.sup)
        respuesta = self.client.post(f"{URL}{transferencia_id}/completar/")
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual((datos["estado"], datos["resuelto_por_username"]), ("COMPLETADA", "sup_t"))
        self.assertEqual(self._stock(), {"Central": 6, "Norte": 24})
        salida = Movimiento.objects.get(pk=datos["movimiento_salida"])
        entrada = Movimiento.objects.get(pk=datos["movimiento_entrada"])
        self.assertEqual((salida.tipo_movimiento, salida.sucursal_id, salida.cantidad_unidades),
                         ("TRANSFERENCIA_SALIDA", self.central.id, 24))
        self.assertEqual((entrada.tipo_movimiento, entrada.sucursal_id), ("TRANSFERENCIA_ENTRADA", self.norte.id))
        self.assertEqual(salida.motivo, f"Transferencia #{transferencia_id}")

    def test_completar_usa_las_unidades_fijadas_al_solicitar(self):
        transferencia_id = self._solicitar(cantidad=1).json()["id"]  # 12 unidades
        Herramienta.objects.filter(pk=self.h.id).update(unidades_por_caja=6)
        self._como(self.admin)
        self.client.post(f"{URL}{transferencia_id}/completar/")
        self.assertEqual(self._stock(), {"Central": 18, "Norte": 12})

    def test_no_se_completa_dos_veces(self):
        transferencia_id = self._solicitar().json()["id"]
        self._como(self.admin)
        self.assertEqual(self.client.post(f"{URL}{transferencia_id}/completar/").status_code, 200)
        segunda = self.client.post(f"{URL}{transferencia_id}/completar/")
        self.assertEqual(segunda.status_code, 409)
        self.assertIn("completada", segunda.json()["detail"])
        self.assertEqual(self._stock(), {"Central": 6, "Norte": 24})

    def test_si_el_stock_ya_no_alcanza_al_completar_no_se_mueve_nada(self):
        transferencia_id = self._solicitar().json()["id"]  # pide 24 de 30
        self._como(self.admin)
        self.client.post("/api/movimientos/", {
            "herramienta": self.h.id, "sucursal": self.central.id,
            "tipo_movimiento": "SALIDA", "tipo_unidad": "UNIDAD", "cantidad": 10,
        }, format="json")  # quedan 20
        respuesta = self.client.post(f"{URL}{transferencia_id}/completar/")
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("Ya no hay stock suficiente", respuesta.json()["detail"])
        self.assertEqual(self._stock(), {"Central": 20, "Norte": 0})
        self.assertEqual(Transferencia.objects.get(pk=transferencia_id).estado, "PENDIENTE")
        self.assertFalse(Movimiento.objects.filter(tipo_movimiento__startswith="TRANSFERENCIA").exists())

    def test_empleado_no_completa_ni_rechaza(self):
        transferencia_id = self._solicitar().json()["id"]
        self.assertEqual(self.client.post(f"{URL}{transferencia_id}/completar/").status_code, 403)
        self.assertEqual(self.client.post(f"{URL}{transferencia_id}/rechazar/", {"motivo": "x"}, format="json").status_code, 403)

    # --- Rechazar ---

    def test_rechazar_con_motivo_no_mueve_stock(self):
        transferencia_id = self._solicitar().json()["id"]
        self._como(self.sup)
        sin_motivo = self.client.post(f"{URL}{transferencia_id}/rechazar/", {"motivo": "  "}, format="json")
        self.assertEqual(sin_motivo.status_code, 400)
        self.assertIn("motivo", sin_motivo.json())
        respuesta = self.client.post(f"{URL}{transferencia_id}/rechazar/", {"motivo": "Norte no tiene espacio"}, format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual((respuesta.json()["estado"], respuesta.json()["motivo_rechazo"]), ("RECHAZADA", "Norte no tiene espacio"))
        self.assertEqual(self._stock(), {"Central": 30, "Norte": 0})
        self.assertEqual(self.client.post(f"{URL}{transferencia_id}/completar/").status_code, 409)

    # --- Listado, inmutabilidad y demanda ---

    def test_listado_filtrado_por_estado(self):
        self._solicitar(cantidad=1)
        rechazada = self._solicitar(cantidad=1).json()["id"]
        self._como(self.admin)
        self.client.post(f"{URL}{rechazada}/rechazar/", {"motivo": "x"}, format="json")
        self.assertEqual(len(self.client.get(URL).json()), 2)
        self.assertEqual([t["estado"] for t in self.client.get(URL, {"estado": "PENDIENTE"}).json()], ["PENDIENTE"])

    def test_no_se_edita_ni_borra(self):
        transferencia_id = self._solicitar().json()["id"]
        self._como(self.admin)
        detalle = f"{URL}{transferencia_id}/"
        self.assertEqual(self.client.patch(detalle, {"cantidad": 1}, format="json").status_code, 405)
        self.assertEqual(self.client.delete(detalle).status_code, 405)

    def test_una_transferencia_no_cuenta_como_venta_en_el_panel(self):
        transferencia_id = self._solicitar().json()["id"]
        self._como(self.admin)
        self.client.post(f"{URL}{transferencia_id}/completar/")
        panel = self.client.get("/api/indicadores/panel/").json()
        self.assertEqual(panel["total_herramientas"], 1)
        from apps.movimientos.domain.stock import cuenta_como_demanda
        from apps.movimientos.domain.value_objects import TipoMovimiento
        self.assertFalse(cuenta_como_demanda(TipoMovimiento.TRANSFERENCIA_SALIDA))
