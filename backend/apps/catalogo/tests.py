"""
Pruebas del catálogo:
  - use_cases con un repositorio falso en memoria (sin base de datos), que
    demuestran que las reglas de negocio no dependen de Django;
  - la API completa (CRUD, validaciones y permisos por rol).

Correr con: python manage.py test apps.catalogo
"""

from dataclasses import replace
from typing import Optional

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.movimientos.infrastructure.models import Movimiento
from apps.usuarios.infrastructure.models import Sucursal, Usuario

from .domain.entities import Herramienta
from .domain.exceptions import (
    CodigoDuplicadoError,
    DatosHerramientaInvalidosError,
    HerramientaNoEncontradaError,
)
from .domain.repositories import HerramientaRepository
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


class GestionarHerramientasUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()

    def _registrar(self, **datos):
        return casos.registrar_herramienta(
            self.repo, {"codigo": "T-1", "nombre": "Taladro", "modelo": "", "unidades_por_caja": 1, **datos}
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
        actualizada = casos.actualizar_herramienta(self.repo, herramienta.id, {"codigo": "T-1", "nombre": "Nuevo"})
        self.assertEqual(actualizada.nombre, "Nuevo")

    def test_actualizar_al_codigo_de_otra_es_duplicado(self):
        self._registrar()
        otra = self._registrar(codigo="T-2")
        with self.assertRaises(CodigoDuplicadoError):
            casos.actualizar_herramienta(self.repo, otra.id, {"codigo": "T-1"})

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
            tipo_movimiento="ENTRADA", tipo_unidad="UNIDAD", cantidad=5,
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
