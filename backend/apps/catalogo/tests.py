"""
Pruebas del catálogo:
  - use_cases con un repositorio falso en memoria (sin base de datos), que
    demuestran que las reglas de negocio no dependen de Django;
  - la API completa (CRUD, validaciones y permisos por rol);
  - HU7: costo unitario con historial (solo el Administrador lo cambia).

Correr con: python manage.py test apps.catalogo
"""

from dataclasses import replace
from typing import Optional

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.movimientos.infrastructure.models import Movimiento
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.value_objects import Rol
from apps.usuarios.infrastructure.models import Sucursal, Usuario

from .domain.entities import Herramienta
from .domain.exceptions import (
    CambioDeCostoNoPermitidoError,
    CodigoDuplicadoError,
    DatosHerramientaInvalidosError,
    HerramientaNoEncontradaError,
)
from .domain.repositories import HerramientaRepository, HistorialCostoRepository
from .infrastructure.models import Herramienta as HerramientaModel
from .use_cases import gestionar_herramientas as casos

URL = "/api/catalogo/herramientas/"


class RepositorioEnMemoria(HerramientaRepository):
    def __init__(self):
        self.datos: dict[int, Herramienta] = {}
        self.siguiente_id = 1

    def obtener_por_id(self, herramienta_id: int) -> Optional[Herramienta]:
        return self.datos.get(herramienta_id)

    def obtener_por_codigo(self, codigo: str) -> Optional[Herramienta]:
        return next((h for h in self.datos.values() if h.codigo == codigo), None)

    def listar(self) -> list[Herramienta]:
        return list(self.datos.values())

    def guardar(self, herramienta: Herramienta) -> Herramienta:
        if herramienta.id is None:
            herramienta = replace(herramienta, id=self.siguiente_id)
            self.siguiente_id += 1
        self.datos[herramienta.id] = herramienta
        return herramienta

    def eliminar(self, herramienta_id: int) -> None:
        del self.datos[herramienta_id]


class HistorialEnMemoria(HistorialCostoRepository):
    def __init__(self):
        self.cambios = []

    def registrar(self, cambio):
        cambio = replace(cambio, id=len(self.cambios) + 1)
        self.cambios.append(cambio)
        return cambio

    def listar_por_herramienta(self, herramienta_id):
        return [c for c in reversed(self.cambios) if c.herramienta_id == herramienta_id]


ADMIN = Actor(usuario_id=1, rol=Rol.ADMINISTRADOR, sucursal_id=None)
SUPERVISOR = Actor(usuario_id=2, rol=Rol.SUPERVISOR, sucursal_id=1)


class GestionarHerramientasUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()
        self.historial = HistorialEnMemoria()

    def _registrar(self, actor=ADMIN, **datos):
        return casos.registrar_herramienta(
            self.repo, {"codigo": "T-1", "nombre": "Taladro", "modelo": "", "unidades_por_caja": 1, **datos},
            actor=actor, historial=self.historial,
        )

    def _actualizar(self, herramienta_id, cambios, actor=ADMIN):
        return casos.actualizar_herramienta(
            self.repo, herramienta_id, cambios, actor=actor, historial=self.historial
        )

    def test_registrar_normaliza_espacios(self):
        herramienta = self._registrar(codigo="  T-1 ", nombre=" Taladro  ")
        self.assertEqual((herramienta.codigo, herramienta.nombre), ("T-1", "Taladro"))

    def test_codigo_duplicado(self):
        self._registrar()
        with self.assertRaises(CodigoDuplicadoError):
            self._registrar(nombre="Otro")

    def test_actualizar_conservando_su_propio_codigo_es_valido(self):
        herramienta = self._registrar()
        actualizada = self._actualizar(herramienta.id, {"codigo": "T-1", "nombre": "Nuevo"})
        self.assertEqual(actualizada.nombre, "Nuevo")

    def test_actualizar_al_codigo_de_otra_es_duplicado(self):
        self._registrar()
        otra = self._registrar(codigo="T-2")
        with self.assertRaises(CodigoDuplicadoError):
            self._actualizar(otra.id, {"codigo": "T-1"})

    def test_reglas_de_datos(self):
        with self.assertRaises(DatosHerramientaInvalidosError) as ctx:
            self._registrar(codigo=" ", unidades_por_caja=0, costo_pedido=-1)
        self.assertEqual(set(ctx.exception.errores), {"codigo", "unidades_por_caja", "costo_pedido"})

    def test_herramienta_inexistente(self):
        with self.assertRaises(HerramientaNoEncontradaError):
            casos.obtener_herramienta(self.repo, 99)
        with self.assertRaises(HerramientaNoEncontradaError):
            casos.eliminar_herramienta(self.repo, 99)


class HerramientaApiTests(APITestCase):
    def setUp(self):
        self.sucursal = Sucursal.objects.create(nombre="Central")
        self.admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.supervisor = Usuario.objects.create_user(
            "sup_test", password="x", rol="SUPERVISOR", sucursal=self.sucursal
        )
        self.empleado = Usuario.objects.create_user(
            "emp_test", password="x", rol="EMPLEADO", sucursal=self.sucursal
        )
        self.client.force_authenticate(self.admin)

    def _crear(self, **datos):
        return self.client.post(URL, {"codigo": "T-1", "nombre": "Taladro", **datos}, format="json")

    # --- Alta (incluye lo del sub-paso 4.1) ---

    def test_crear_sin_campos_eoq_sigue_funcionando(self):
        respuesta = self._crear()
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertEqual(datos["unidades_por_caja"], 1)
        for campo in ["demanda_anual", "costo_pedido", "costo_almacenamiento_unitario", "tiempo_entrega_dias"]:
            self.assertIsNone(datos[campo])

    def test_crear_con_campos_eoq_devuelve_numeros(self):
        respuesta = self._crear(
            unidades_por_caja=12, demanda_anual=1000, costo_pedido="50.00",
            costo_almacenamiento_unitario=2.5, tiempo_entrega_dias=10,
        )
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertEqual(datos["costo_pedido"], 50)
        self.assertEqual(datos["costo_almacenamiento_unitario"], 2.5)

    def test_valores_negativos_y_caja_cero_son_400(self):
        for campo, valor in [("demanda_anual", -1), ("costo_pedido", -1),
                             ("costo_almacenamiento_unitario", -1), ("tiempo_entrega_dias", -1),
                             ("unidades_por_caja", 0)]:
            with self.subTest(campo=campo):
                respuesta = self._crear(codigo=f"N-{campo}", **{campo: valor})
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.json())

    def test_codigo_duplicado_es_400_en_el_campo_codigo(self):
        self._crear()
        respuesta = self._crear(nombre="Otro")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("codigo", respuesta.json())

    # --- Lectura, edición y borrado ---

    def test_listar_y_obtener(self):
        herramienta_id = self._crear().json()["id"]
        self.assertEqual(len(self.client.get(URL).json()), 1)
        self.assertEqual(self.client.get(f"{URL}{herramienta_id}/").json()["codigo"], "T-1")
        self.assertEqual(self.client.get(f"{URL}999/").status_code, 404)
        self.assertEqual(self.client.get(f"{URL}abc/").status_code, 404)

    def test_patch_solo_cambia_lo_enviado(self):
        herramienta_id = self._crear(unidades_por_caja=12, demanda_anual=500).json()["id"]
        respuesta = self.client.patch(f"{URL}{herramienta_id}/", {"nombre": "Taladro X"}, format="json")
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(datos["nombre"], "Taladro X")
        self.assertEqual(datos["unidades_por_caja"], 12)
        self.assertEqual(datos["demanda_anual"], 500)

    def test_put_reemplaza_y_puede_vaciar_campos_eoq(self):
        herramienta_id = self._crear(demanda_anual=500).json()["id"]
        respuesta = self.client.put(
            f"{URL}{herramienta_id}/",
            {"codigo": "T-1", "nombre": "Taladro", "unidades_por_caja": 6, "demanda_anual": None},
            format="json",
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["unidades_por_caja"], 6)
        self.assertIsNone(respuesta.json()["demanda_anual"])

    def test_editar_al_codigo_de_otra_es_400(self):
        self._crear()
        otra_id = self._crear(codigo="T-2").json()["id"]
        respuesta = self.client.patch(f"{URL}{otra_id}/", {"codigo": "T-1"}, format="json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("codigo", respuesta.json())

    def test_eliminar(self):
        herramienta_id = self._crear().json()["id"]
        self.assertEqual(self.client.delete(f"{URL}{herramienta_id}/").status_code, 204)
        self.assertEqual(self.client.delete(f"{URL}{herramienta_id}/").status_code, 404)

    def test_eliminar_con_movimientos_es_409(self):
        herramienta_id = self._crear().json()["id"]
        Movimiento.objects.create(
            herramienta_id=herramienta_id, sucursal=self.sucursal, usuario=self.admin,
            tipo_movimiento="ENTRADA", tipo_unidad="UNIDAD", cantidad=5, cantidad_unidades=5,
        )
        respuesta = self.client.delete(f"{URL}{herramienta_id}/")
        self.assertEqual(respuesta.status_code, 409)
        self.assertTrue(HerramientaModel.objects.filter(pk=herramienta_id).exists())

    # --- Permisos por rol ---

    def test_empleado_puede_leer_pero_no_escribir(self):
        herramienta_id = self._crear().json()["id"]
        self.client.force_authenticate(self.empleado)
        detalle = f"{URL}{herramienta_id}/"

        self.assertEqual(self.client.get(URL).status_code, 200)
        self.assertEqual(self.client.get(detalle).status_code, 200)
        self.assertEqual(self._crear(codigo="E-1").status_code, 403)
        self.assertEqual(self.client.put(detalle, {"codigo": "T-1", "nombre": "x"}, format="json").status_code, 403)
        self.assertEqual(self.client.patch(detalle, {"nombre": "x"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(detalle).status_code, 403)
        self.assertEqual(HerramientaModel.objects.get(pk=herramienta_id).nombre, "Taladro")

    def test_supervisor_puede_escribir(self):
        self.client.force_authenticate(self.supervisor)
        herramienta_id = self._crear().json()["id"]
        detalle = f"{URL}{herramienta_id}/"
        self.assertEqual(self.client.patch(detalle, {"nombre": "x"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(detalle).status_code, 204)

    def test_sin_sesion_es_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(URL).status_code, 401)


# --- HU7: costo unitario con historial ---

from decimal import Decimal


class CostoUnitarioUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()
        self.historial = HistorialEnMemoria()

    def _registrar(self, actor=ADMIN, **datos):
        return casos.registrar_herramienta(
            self.repo, {"codigo": "T-1", "nombre": "Taladro", "modelo": "", "unidades_por_caja": 1, **datos},
            actor=actor, historial=self.historial,
        )

    def _actualizar(self, herramienta_id, cambios, actor=ADMIN):
        return casos.actualizar_herramienta(self.repo, herramienta_id, cambios, actor=actor, historial=self.historial)

    def test_alta_con_costo_registra_el_primer_valor(self):
        herramienta = self._registrar(costo_unitario=Decimal("10.50"))
        [cambio] = self.historial.cambios
        self.assertEqual((cambio.herramienta_id, cambio.costo_anterior, cambio.costo_nuevo, cambio.usuario_id),
                         (herramienta.id, None, Decimal("10.50"), ADMIN.usuario_id))

    def test_alta_sin_costo_no_registra_historial(self):
        self._registrar()
        self.assertEqual(self.historial.cambios, [])

    def test_cambio_de_costo_guarda_anterior_y_nuevo(self):
        herramienta = self._registrar(costo_unitario=Decimal("10"))
        self._actualizar(herramienta.id, {"costo_unitario": Decimal("12.75")})
        ultimo = self.historial.listar_por_herramienta(herramienta.id)[0]
        self.assertEqual((ultimo.costo_anterior, ultimo.costo_nuevo), (Decimal("10"), Decimal("12.75")))

    def test_editar_otros_campos_no_toca_el_historial(self):
        herramienta = self._registrar(costo_unitario=Decimal("10"))
        self._actualizar(herramienta.id, {"nombre": "Taladro grande", "costo_unitario": Decimal("10.00")})
        self.assertEqual(len(self.historial.cambios), 1)

    def test_costo_cero_o_negativo_es_invalido(self):
        for valor in (Decimal("0"), Decimal("-1")):
            with self.assertRaises(DatosHerramientaInvalidosError, msg=valor) as ctx:
                self._registrar(costo_unitario=valor)
            self.assertIn("costo_unitario", ctx.exception.errores)

    def test_no_se_puede_quitar_un_costo_cargado(self):
        herramienta = self._registrar(costo_unitario=Decimal("10"))
        with self.assertRaises(DatosHerramientaInvalidosError):
            self._actualizar(herramienta.id, {"costo_unitario": None})

    def test_supervisor_no_cambia_el_costo_pero_edita_lo_demas(self):
        herramienta = self._registrar(costo_unitario=Decimal("10"))
        with self.assertRaises(CambioDeCostoNoPermitidoError):
            self._actualizar(herramienta.id, {"costo_unitario": Decimal("11")}, actor=SUPERVISOR)
        with self.assertRaises(CambioDeCostoNoPermitidoError):
            self._registrar(actor=SUPERVISOR, codigo="T-2", costo_unitario=Decimal("5"))
        # Mismo costo (el formulario siempre lo reenvía): no es un cambio.
        editada = self._actualizar(herramienta.id, {"nombre": "Otro", "costo_unitario": Decimal("10")}, actor=SUPERVISOR)
        self.assertEqual(editada.nombre, "Otro")
        self.assertEqual(len(self.historial.cambios), 1)


class CostoUnitarioApiTests(APITestCase):
    def setUp(self):
        self.sucursal = Sucursal.objects.create(nombre="Central")
        self.admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.supervisor = Usuario.objects.create_user("sup_test", password="x", rol="SUPERVISOR", sucursal=self.sucursal)
        self.empleado = Usuario.objects.create_user("emp_test", password="x", rol="EMPLEADO", sucursal=self.sucursal)
        self.client.force_authenticate(self.admin)
        respuesta = self.client.post(URL, {"codigo": "T-1", "nombre": "Taladro", "costo_unitario": "10.50"}, format="json")
        self.herramienta_id = respuesta.json()["id"]

    def _url(self, sufijo=""):
        return f"{URL}{self.herramienta_id}/{sufijo}"

    def test_alta_devuelve_el_costo_como_numero_y_lo_registra(self):
        self.assertEqual(self.client.get(self._url()).json()["costo_unitario"], 10.5)
        historial = self.client.get(self._url("historial-costos/")).json()
        self.assertEqual(len(historial), 1)
        self.assertEqual((historial[0]["costo_anterior"], historial[0]["costo_nuevo"], historial[0]["usuario"]),
                         (None, 10.5, "admin_test"))

    def test_admin_cambia_el_costo_y_queda_el_historial_ordenado(self):
        self.client.patch(self._url(), {"costo_unitario": "12.00"}, format="json")
        self.client.patch(self._url(), {"costo_unitario": "13.25"}, format="json")
        historial = self.client.get(self._url("historial-costos/")).json()
        self.assertEqual([(h["costo_anterior"], h["costo_nuevo"]) for h in historial],
                         [(12, 13.25), (10.5, 12), (None, 10.5)])

    def test_supervisor_que_cambia_el_costo_recibe_403_y_nada_cambia(self):
        self.client.force_authenticate(self.supervisor)
        respuesta = self.client.patch(self._url(), {"nombre": "Otro", "costo_unitario": "99"}, format="json")
        self.assertEqual(respuesta.status_code, 403)
        self.assertIn("Administrador", respuesta.json()["detail"])
        self.assertEqual(HerramientaModel.objects.get(pk=self.herramienta_id).nombre, "Taladro")

    def test_supervisor_edita_otros_campos_reenviando_el_mismo_costo(self):
        self.client.force_authenticate(self.supervisor)
        datos = self.client.get(self._url()).json()
        datos["nombre"] = "Taladro percutor"
        respuesta = self.client.put(self._url(), datos, format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(self.client.get(self._url("historial-costos/")).json()), 1)

    def test_costo_cero_es_400(self):
        respuesta = self.client.patch(self._url(), {"costo_unitario": "0"}, format="json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("costo_unitario", respuesta.json())

    def test_costo_no_numerico_es_400(self):
        respuesta = self.client.patch(self._url(), {"costo_unitario": "diez"}, format="json")
        self.assertEqual(respuesta.status_code, 400)

    def test_empleado_ve_el_historial_pero_no_edita(self):
        self.client.force_authenticate(self.empleado)
        self.assertEqual(self.client.get(self._url("historial-costos/")).status_code, 200)
        self.assertEqual(self.client.patch(self._url(), {"costo_unitario": "11"}, format="json").status_code, 403)

    def test_historial_de_herramienta_inexistente_es_404(self):
        self.assertEqual(self.client.get(f"{URL}9999/historial-costos/").status_code, 404)

    def test_historial_en_una_sola_consulta(self):
        for valor in ("11", "12", "13"):
            self.client.patch(self._url(), {"costo_unitario": valor}, format="json")
        # 1: existe la herramienta; 1: historial con el usuario (select_related)
        with self.assertNumQueries(2):
            self.client.get(self._url("historial-costos/"))

    def test_herramienta_con_historial_no_se_elimina(self):
        respuesta = self.client.delete(self._url())
        self.assertEqual(respuesta.status_code, 409)
        self.assertTrue(HerramientaModel.objects.filter(pk=self.herramienta_id).exists())
