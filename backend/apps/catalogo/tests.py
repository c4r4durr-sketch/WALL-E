"""
Pruebas del catálogo:
  - use_cases con un repositorio falso en memoria (sin base de datos), que
    demuestran que las reglas de negocio no dependen de Django;
  - la API completa (CRUD, validaciones y permisos por rol);
  - HU7: costo unitario con historial (solo el Administrador lo cambia);
  - foto del producto: obligatoria en el alta, JPG/PNG/WebP de hasta 5 MB;
  - comando cargar_demo (datos de ejemplo para la demo).

Correr con: python manage.py test apps.catalogo
"""

import io
import shutil
import tempfile
from dataclasses import replace
from typing import Optional

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from apps.auditoria.infrastructure.models import HistorialModificacion
from apps.indicadores.use_cases.clasificar_abc import clasificar_abc
from apps.indicadores.use_cases.panel_auditoria import construir_panel
from apps.movimientos.domain.stock import stock_desde_totales
from apps.movimientos.infrastructure.models import Movimiento
from apps.movimientos.infrastructure.repositories import MovimientoRepositoryDjango
from apps.proveedores.domain.entities import Proveedor
from apps.proveedores.domain.repositories import ProveedorRepository
from apps.proveedores.infrastructure.models import Proveedor as ProveedorModel
from apps.transferencias.infrastructure.models import Transferencia
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.value_objects import Rol
from apps.usuarios.infrastructure.models import Sucursal, Usuario
from apps.usuarios.infrastructure.repositories import SucursalRepositoryDjango

from .domain.entities import Herramienta
from .domain.exceptions import (
    CambioDeCostoNoPermitidoError,
    CodigoDuplicadoError,
    DatosHerramientaInvalidosError,
    HerramientaNoEncontradaError,
)
from .domain.repositories import HerramientaRepository, HistorialCostoRepository
from .infrastructure.models import Herramienta as HerramientaModel
from .infrastructure.models import HistorialCosto, Promocion
from .infrastructure.repositories import HerramientaRepositoryDjango, PromocionRepositoryDjango
from .use_cases import gestionar_herramientas as casos

URL = "/api/catalogo/herramientas/"


def imagen_de_prueba(formato: str = "PNG", nombre: str = "foto.png", relleno: int = 0) -> SimpleUploadedFile:
    """Una imagen real (Pillow la puede abrir) de 8x8. `relleno` agrega
    bytes al final para simular un archivo pesado sin dibujar uno enorme.
    La usan también las pruebas de proveedores y auditoría que dan de alta
    herramientas por la API."""
    salida = io.BytesIO()
    Image.new("RGB", (8, 8), "#C2410C").save(salida, format=formato)
    return SimpleUploadedFile(nombre, salida.getvalue() + b"\0" * relleno)


class MediaTemporal:
    """Mixin para pruebas que suben fotos: las guarda en una carpeta
    temporal (no en backend/media/) que se borra al terminar la clase."""

    @classmethod
    def setUpClass(cls):
        carpeta = tempfile.mkdtemp(prefix="walle-media-")
        ajuste = override_settings(MEDIA_ROOT=carpeta)
        ajuste.enable()
        cls.addClassCleanup(shutil.rmtree, carpeta, ignore_errors=True)
        cls.addClassCleanup(ajuste.disable)
        super().setUpClass()


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

    def guardar(self, herramienta: Herramienta, imagen=None) -> Herramienta:
        if herramienta.id is None:
            herramienta = replace(herramienta, id=self.siguiente_id)
            self.siguiente_id += 1
        if imagen is not None:
            herramienta = replace(herramienta, imagen=f"productos/{imagen.nombre}")
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


class ProveedoresEnMemoria(ProveedorRepository):
    """Proveedor 1 activo y 2 inactivo; solo se usa obtener_por_id."""

    def __init__(self):
        self.datos = {1: Proveedor(1, "Ferretera Andina", "2223344"),
                      2: Proveedor(2, "Importadora Cerrada", "2223355", activo=False)}

    def obtener_por_id(self, proveedor_id):
        return self.datos.get(proveedor_id)

    def obtener_por_nombre(self, nombre):
        return None

    def listar(self, buscar="", solo_activos=False):
        return list(self.datos.values())

    def guardar(self, proveedor):
        return proveedor

    def eliminar(self, proveedor_id):
        pass


ADMIN = Actor(usuario_id=1, rol=Rol.ADMINISTRADOR, sucursal_id=None)
SUPERVISOR = Actor(usuario_id=2, rol=Rol.SUPERVISOR, sucursal_id=1)


class GestionarHerramientasUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()
        self.historial = HistorialEnMemoria()
        self.proveedores = ProveedoresEnMemoria()

    def _registrar(self, actor=ADMIN, **datos):
        return casos.registrar_herramienta(
            self.repo, {"codigo": "T-1", "nombre": "Taladro", "modelo": "", "unidades_por_caja": 1, **datos},
            actor=actor, historial=self.historial, proveedores=self.proveedores,
        )

    def _actualizar(self, herramienta_id, cambios, actor=ADMIN):
        return casos.actualizar_herramienta(
            self.repo, herramienta_id, cambios, actor=actor, historial=self.historial, proveedores=self.proveedores
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


class HerramientaApiTests(MediaTemporal, APITestCase):
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
        datos = {"codigo": "T-1", "nombre": "Taladro", "imagen": imagen_de_prueba(), **datos}
        return self.client.post(URL, datos, format="multipart")

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
        self.proveedores = ProveedoresEnMemoria()

    def _registrar(self, actor=ADMIN, **datos):
        return casos.registrar_herramienta(
            self.repo, {"codigo": "T-1", "nombre": "Taladro", "modelo": "", "unidades_por_caja": 1, **datos},
            actor=actor, historial=self.historial, proveedores=self.proveedores,
        )

    def _actualizar(self, herramienta_id, cambios, actor=ADMIN):
        return casos.actualizar_herramienta(self.repo, herramienta_id, cambios, actor=actor, historial=self.historial, proveedores=self.proveedores)

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


class CostoUnitarioApiTests(MediaTemporal, APITestCase):
    def setUp(self):
        self.sucursal = Sucursal.objects.create(nombre="Central")
        self.admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.supervisor = Usuario.objects.create_user("sup_test", password="x", rol="SUPERVISOR", sucursal=self.sucursal)
        self.empleado = Usuario.objects.create_user("emp_test", password="x", rol="EMPLEADO", sucursal=self.sucursal)
        self.client.force_authenticate(self.admin)
        respuesta = self.client.post(
            URL, {"codigo": "T-1", "nombre": "Taladro", "costo_unitario": "10.50", "imagen": imagen_de_prueba()},
            format="multipart",
        )
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


# --- Foto del producto ---

from .domain.entities import ImagenProducto


class FotoUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()

    def _registrar(self, imagen, codigo="T-1"):
        return casos.registrar_herramienta(
            self.repo, {"codigo": codigo, "nombre": "Taladro", "modelo": "", "unidades_por_caja": 1},
            actor=ADMIN, historial=HistorialEnMemoria(), proveedores=ProveedoresEnMemoria(), imagen=imagen,
        )

    def test_acepta_jpg_png_y_webp(self):
        for formato in ("JPEG", "PNG", "WEBP"):
            herramienta = self._registrar(ImagenProducto(f"f.{formato}", formato, 1000), codigo=formato)
            self.assertEqual(herramienta.imagen, f"productos/f.{formato}")

    def test_otro_formato_es_invalido_y_no_guarda_nada(self):
        with self.assertRaises(DatosHerramientaInvalidosError) as ctx:
            self._registrar(ImagenProducto("f.gif", "GIF", 1000))
        self.assertIn("imagen", ctx.exception.errores)
        self.assertEqual(self.repo.datos, {})

    def test_hasta_5_mb_exactos(self):
        herramienta = self._registrar(ImagenProducto("f", "PNG", 5 * 1024 * 1024))
        with self.assertRaises(DatosHerramientaInvalidosError):
            casos.actualizar_herramienta(
                self.repo, herramienta.id, {}, actor=ADMIN, historial=HistorialEnMemoria(),
                proveedores=ProveedoresEnMemoria(), imagen=ImagenProducto("g", "PNG", 5 * 1024 * 1024 + 1),
            )
        self.assertEqual(self.repo.obtener_por_id(herramienta.id).imagen, "productos/f")

    def test_herramientas_sin_foto(self):
        self.repo.guardar(Herramienta(None, "V-1", "Vieja", "", 1))
        self._registrar(ImagenProducto("f", "PNG", 10))
        self.assertEqual([h.codigo for h in casos.herramientas_sin_foto(self.repo)], ["V-1"])


class FotoApiTests(MediaTemporal, APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.client.force_authenticate(self.admin)

    def _crear(self, **datos):
        return self.client.post(URL, {"codigo": "T-1", "nombre": "Taladro", **datos}, format="multipart")

    def test_alta_con_foto_devuelve_url_absoluta_en_el_detalle_y_el_listado(self):
        respuesta = self._crear(imagen=imagen_de_prueba("JPEG", "mi foto.jpg"), unidades_por_caja="12")
        self.assertEqual(respuesta.status_code, 201, respuesta.content)
        url = respuesta.json()["imagen"]
        self.assertRegex(url, r"^http://testserver/media/productos/t-1.*\.jpg$")
        self.assertEqual(respuesta.json()["unidades_por_caja"], 12)
        [fila] = self.client.get(URL).json()
        self.assertEqual(fila["imagen"], url)

    def test_alta_sin_foto_es_400(self):
        for formato in ("multipart", "json"):
            with self.subTest(formato=formato):
                respuesta = self.client.post(URL, {"codigo": "T-1", "nombre": "Taladro"}, format=formato)
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(respuesta.json()["imagen"], ["La foto del producto es obligatoria."])
        self.assertFalse(HerramientaModel.objects.exists())

    def test_archivo_que_no_es_imagen_es_400(self):
        respuesta = self._crear(imagen=SimpleUploadedFile("foto.png", b"no soy una imagen"))
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("imagen", respuesta.json())

    def test_formato_no_permitido_es_400(self):
        respuesta = self._crear(imagen=imagen_de_prueba("GIF", "foto.gif"))
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("JPG, PNG, WebP", respuesta.json()["imagen"][0])
        self.assertFalse(HerramientaModel.objects.exists())

    def test_archivo_mayor_a_5_mb_es_400(self):
        respuesta = self._crear(imagen=imagen_de_prueba(relleno=5 * 1024 * 1024))
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("5 MB", respuesta.json()["imagen"][0])
        self.assertFalse(HerramientaModel.objects.exists())

    def test_webp_es_valido(self):
        self.assertEqual(self._crear(imagen=imagen_de_prueba("WEBP", "foto.webp")).status_code, 201)

    def test_editar_sin_foto_la_conserva_y_con_foto_la_reemplaza(self):
        creada = self._crear(imagen=imagen_de_prueba()).json()
        detalle = f"{URL}{creada['id']}/"
        # Reenviar los datos tal como vinieron (con la URL) no toca la foto.
        respuesta = self.client.put(detalle, {**creada, "nombre": "Taladro X"}, format="json")
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.assertEqual(respuesta.json()["imagen"], creada["imagen"])

        anterior = HerramientaModel.objects.get(pk=creada["id"]).imagen
        with self.captureOnCommitCallbacks(execute=True):
            respuesta = self.client.patch(detalle, {"imagen": imagen_de_prueba("JPEG", "nueva.jpg")}, format="multipart")
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotEqual(respuesta.json()["imagen"], creada["imagen"])
        self.assertFalse(anterior.storage.exists(anterior.name))

    def test_herramienta_antigua_sin_foto_devuelve_null(self):
        HerramientaModel.objects.create(codigo="V-1", nombre="Vieja")
        self.assertIsNone(self.client.get(URL).json()[0]["imagen"])

    def test_cargar_fotos_demo_solo_completa_las_que_no_tienen(self):
        con_foto = self._crear(imagen=imagen_de_prueba()).json()
        HerramientaModel.objects.create(codigo="V-1", nombre="Vieja")
        call_command("cargar_fotos_demo", stdout=io.StringIO())
        filas = {h["codigo"]: h["imagen"] for h in self.client.get(URL).json()}
        self.assertEqual(filas["T-1"], con_foto["imagen"])
        self.assertRegex(filas["V-1"], r"\.png$")
        salida = io.StringIO()
        call_command("cargar_fotos_demo", stdout=salida)
        self.assertIn(": 0.", salida.getvalue())


class CargarDemoTests(MediaTemporal, TestCase):
    """Comando cargar_demo: reemplaza solo el inventario, se puede correr
    dos veces y deja los casos que la demo necesita ver."""

    @classmethod
    def setUpTestData(cls):
        cls.central = Sucursal.objects.create(nombre="Central")
        cls.norte = Sucursal.objects.create(nombre="Norte")
        cls.admin = Usuario.objects.create_user("admin_demo", password="x", rol="ADMINISTRADOR")
        Usuario.objects.create_user("emp_demo", password="x", rol="EMPLEADO", sucursal=cls.central)
        Usuario.objects.create_user("sup_demo", password="x", rol="SUPERVISOR", sucursal=cls.norte)
        # Inventario previo, que --reiniciar debe reemplazar.
        vieja = HerramientaModel.objects.create(codigo="VIEJA", nombre="Herramienta previa")
        Movimiento.objects.create(
            herramienta=vieja, sucursal=cls.central, usuario=cls.admin, tipo_movimiento="ENTRADA",
            tipo_unidad="UNIDAD", cantidad=5, cantidad_unidades=5,
        )
        cls.usuarios_antes = cls._usuarios()
        cls.auditoria_antes = set(HistorialModificacion.objects.values_list("id", flat=True))
        call_command("cargar_demo", "--reiniciar", stdout=io.StringIO())
        cls.conteo_despues = cls._conteo()

    @staticmethod
    def _usuarios():
        return list(
            Usuario.objects.order_by("id").values_list("id", "username", "password", "rol", "sucursal_id", "is_active")
        )

    @staticmethod
    def _conteo():
        return {
            "herramientas": HerramientaModel.objects.count(),
            "proveedores": ProveedorModel.objects.count(),
            "movimientos": Movimiento.objects.count(),
            "transferencias": Transferencia.objects.count(),
            "promociones": Promocion.objects.count(),
            "costos": HistorialCosto.objects.count(),
        }

    def test_no_toca_usuarios_sucursales_ni_auditoria(self):
        self.assertEqual(self._usuarios(), self.usuarios_antes)
        self.assertEqual(list(Sucursal.objects.order_by("id").values_list("nombre", flat=True)), ["Central", "Norte"])
        restantes = set(HistorialModificacion.objects.values_list("id", flat=True))
        self.assertTrue(self.auditoria_antes <= restantes)
        # Lo que hizo el comando queda firmado como cargar_demo (sin usuario).
        nuevos = HistorialModificacion.objects.exclude(id__in=self.auditoria_antes)
        self.assertEqual(set(nuevos.values_list("usuario_id", "usuario_username")), {(None, "cargar_demo")})
        self.assertFalse(HerramientaModel.objects.filter(codigo="VIEJA").exists())

    def test_catalogo_completo_con_foto_proveedor_y_datos_eoq(self):
        self.assertEqual(self.conteo_despues["proveedores"], 4)
        self.assertEqual(self.conteo_despues["herramientas"], 20)
        fotos = set()
        for h in HerramientaModel.objects.all():
            for campo in ("modelo", "unidades_por_caja", "costo_unitario", "proveedor_id", "demanda_anual",
                          "costo_pedido", "costo_almacenamiento_unitario", "tiempo_entrega_dias"):
                self.assertTrue(getattr(h, campo), f"{h.codigo} sin {campo}")
            with h.imagen.open("rb") as archivo:
                fotos.add(archivo.read())
        self.assertEqual(len(fotos), 20)
        # Tres herramientas cambiaron de precio: alta + cambio en el historial.
        self.assertEqual(self.conteo_despues["costos"], 23)

    def test_doce_meses_de_entradas_salidas_y_transferencias(self):
        hoy = timezone.localdate()
        primera = timezone.localtime(Movimiento.objects.order_by("creado_en").first().creado_en).date()
        self.assertTrue(355 <= (hoy - primera).days <= 366)
        tipos = set(Movimiento.objects.values_list("tipo_movimiento", flat=True))
        self.assertTrue({"ENTRADA", "SALIDA", "TRANSFERENCIA_SALIDA", "TRANSFERENCIA_ENTRADA"} <= tipos)
        estados = set(Transferencia.objects.values_list("estado", flat=True))
        self.assertEqual(estados, {"COMPLETADA", "PENDIENTE", "RECHAZADA"})
        for fila in MovimientoRepositoryDjango().resumen_inventario():
            self.assertGreaterEqual(stock_desde_totales(fila.unidades_por_tipo), 0)

    def test_deja_alertas_estancadas_abc_y_una_promocion(self):
        hoy = timezone.localdate()
        movimientos, herramientas = MovimientoRepositoryDjango(), HerramientaRepositoryDjango()
        panel = construir_panel(movimientos, herramientas, SucursalRepositoryDjango(), hoy, timezone.now())
        self.assertTrue({"CIN-8M", "ALI-PUN6", "NIV-24", "TAL-13"} <= {a.codigo for a in panel.alertas})
        estancadas = {e.codigo for e in panel.estancadas}
        self.assertTrue({"LLA-TUBO", "NIV-LAS", "SIE-CIR", "ATO-12V"} <= estancadas)
        dias = {(e.codigo, e.sucursal_id): e.dias_sin_venta for e in panel.estancadas}
        self.assertEqual(dias[("LLA-TUBO", self.central.id)], 55)
        self.assertEqual(dias[("NIV-LAS", self.norte.id)], 87)
        self.assertEqual(dias[("ATO-12V", self.central.id)], 100)
        clases = [c.clase for c in clasificar_abc(herramientas, movimientos, timezone.now())]
        self.assertTrue(all(clases.count(clase) >= 3 for clase in "ABC"), clases)

        vigentes = [p for p in PromocionRepositoryDjango().listar() if p.vigente(hoy)]
        self.assertEqual([p.herramienta_codigo for p in vigentes], ["SIE-CIR"])
        self.assertIn("SIE-CIR", estancadas)

    def test_sin_reiniciar_no_hace_nada_si_ya_hay_herramientas(self):
        salida = io.StringIO()
        call_command("cargar_demo", stdout=salida)
        self.assertIn("no se hizo nada", salida.getvalue())
        self.assertEqual(self._conteo(), self.conteo_despues)

    def test_reiniciar_dos_veces_deja_lo_mismo(self):
        def detalle():
            return sorted(Movimiento.objects.values_list("herramienta__codigo", "tipo_movimiento", "cantidad_unidades"))

        antes = detalle()
        call_command("cargar_demo", "--reiniciar", stdout=io.StringIO())
        self.assertEqual(self._conteo(), self.conteo_despues)
        self.assertEqual(detalle(), antes)
        self.assertEqual(self._usuarios(), self.usuarios_antes)

    def test_sin_administrador_activo_no_cambia_nada(self):
        Usuario.objects.filter(rol="ADMINISTRADOR").update(is_active=False)
        with self.assertRaises(CommandError):
            call_command("cargar_demo", "--reiniciar", stdout=io.StringIO())
        self.assertEqual(self._conteo(), self.conteo_despues)
