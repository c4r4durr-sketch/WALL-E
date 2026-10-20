"""
Pruebas del directorio de proveedores (HU8):
  - casos de uso con un repositorio falso en memoria (sin base de datos);
  - la API (CRUD, búsqueda, permisos por rol, 409 con herramientas);
  - la relación con el catálogo (solo se asignan proveedores activos).

Correr con: python manage.py test apps.proveedores
"""

from dataclasses import replace
from typing import Optional

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.catalogo.infrastructure.models import Herramienta as HerramientaModel
from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.value_objects import Rol
from apps.usuarios.infrastructure.models import Sucursal, Usuario

from .domain.entities import Proveedor
from .domain.exceptions import (
    DatosProveedorInvalidosError,
    NombreProveedorDuplicadoError,
    PermisoDenegadoError,
    ProveedorNoEncontradoError,
)
from .domain.repositories import ProveedorRepository
from .infrastructure.models import Proveedor as ProveedorModel
from .use_cases import gestionar_proveedores as casos

URL = "/api/proveedores/"
URL_CATALOGO = "/api/catalogo/herramientas/"

ADMIN = Actor(usuario_id=1, rol=Rol.ADMINISTRADOR, sucursal_id=None)
SUPERVISOR = Actor(usuario_id=2, rol=Rol.SUPERVISOR, sucursal_id=1)


class RepositorioEnMemoria(ProveedorRepository):
    def __init__(self):
        self.datos: dict[int, Proveedor] = {}

    def obtener_por_id(self, proveedor_id: int) -> Optional[Proveedor]:
        return self.datos.get(proveedor_id)

    def obtener_por_nombre(self, nombre: str) -> Optional[Proveedor]:
        return next((p for p in self.datos.values() if p.nombre.lower() == nombre.lower()), None)

    def listar(self, buscar: str = "", solo_activos: bool = False) -> list[Proveedor]:
        return sorted(
            (p for p in self.datos.values()
             if buscar.lower() in p.nombre.lower() and (p.activo or not solo_activos)),
            key=lambda p: p.nombre,
        )

    def guardar(self, proveedor: Proveedor) -> Proveedor:
        if proveedor.id is None:
            proveedor = replace(proveedor, id=len(self.datos) + 1)
        self.datos[proveedor.id] = proveedor
        return proveedor

    def eliminar(self, proveedor_id: int) -> None:
        del self.datos[proveedor_id]


class GestionarProveedoresTests(SimpleTestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()

    def _registrar(self, actor=ADMIN, **datos):
        return casos.registrar_proveedor(
            self.repo, actor, {"nombre": "Ferretera Andina", "telefono": "+591 2 2123456", **datos}
        )

    def test_registrar_normaliza(self):
        proveedor = self._registrar(nombre="  Ferretera   Andina ", email=" Ventas@Andina.BO ")
        self.assertEqual((proveedor.nombre, proveedor.email), ("Ferretera Andina", "ventas@andina.bo"))

    def test_nombre_duplicado_sin_distinguir_mayusculas(self):
        self._registrar()
        with self.assertRaises(NombreProveedorDuplicadoError):
            self._registrar(nombre="FERRETERA ANDINA")

    def test_actualizar_conservando_su_nombre_es_valido(self):
        proveedor = self._registrar()
        actualizado = casos.actualizar_proveedor(self.repo, ADMIN, proveedor.id, {"telefono": "77712345"})
        self.assertEqual(actualizado.telefono, "77712345")

    def test_datos_obligatorios_y_formatos(self):
        with self.assertRaises(DatosProveedorInvalidosError) as ctx:
            self._registrar(nombre=" ", telefono="", email="no-es-correo")
        self.assertEqual(set(ctx.exception.errores), {"nombre", "telefono", "email"})

    def test_telefonos(self):
        for telefono in ("77712345", "+591 777-12345", "(2) 2123456"):
            with self.subTest(telefono=telefono):
                self.repo = RepositorioEnMemoria()
                self.assertEqual(self._registrar(telefono=telefono).telefono, telefono)
        for telefono in ("12345", "abc1234567", "1234567890123456"):
            with self.subTest(telefono=telefono), self.assertRaises(DatosProveedorInvalidosError):
                self._registrar(telefono=telefono)

    def test_solo_el_administrador_escribe(self):
        with self.assertRaises(PermisoDenegadoError):
            self._registrar(actor=SUPERVISOR)
        proveedor = self._registrar()
        with self.assertRaises(PermisoDenegadoError):
            casos.actualizar_proveedor(self.repo, SUPERVISOR, proveedor.id, {"activo": False})
        with self.assertRaises(PermisoDenegadoError):
            casos.eliminar_proveedor(self.repo, SUPERVISOR, proveedor.id)

    def test_buscar_y_filtrar_activos(self):
        self._registrar(nombre="Ferretera Andina")
        self._registrar(nombre="Herramientas del Sur")
        inactivo = self._registrar(nombre="Ferrosur")
        casos.actualizar_proveedor(self.repo, ADMIN, inactivo.id, {"activo": False})
        self.assertEqual([p.nombre for p in casos.listar_proveedores(self.repo, buscar=" ferr ")],
                         ["Ferretera Andina", "Ferrosur"])
        self.assertEqual([p.nombre for p in casos.listar_proveedores(self.repo, buscar="ferr", solo_activos=True)],
                         ["Ferretera Andina"])

    def test_inexistente(self):
        with self.assertRaises(ProveedorNoEncontradoError):
            casos.obtener_proveedor(self.repo, 99)
        with self.assertRaises(ProveedorNoEncontradoError):
            casos.eliminar_proveedor(self.repo, ADMIN, 99)


class ProveedorApiTests(APITestCase):
    def setUp(self):
        self.sucursal = Sucursal.objects.create(nombre="Central")
        self.admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.supervisor = Usuario.objects.create_user("sup", password="x", rol="SUPERVISOR", sucursal=self.sucursal)
        self.empleado = Usuario.objects.create_user("emp", password="x", rol="EMPLEADO", sucursal=self.sucursal)
        self.client.force_authenticate(self.admin)

    def _crear(self, **datos):
        return self.client.post(
            URL, {"nombre": "Ferretera Andina", "telefono": "77712345", "email": "ventas@andina.bo", **datos},
            format="json",
        )

    def test_crud_completo(self):
        creado = self._crear()
        self.assertEqual(creado.status_code, 201)
        proveedor_id = creado.json()["id"]
        self.assertEqual(creado.json()["cantidad_herramientas"], 0)
        editado = self.client.patch(f"{URL}{proveedor_id}/", {"telefono": "22123456"}, format="json")
        self.assertEqual(editado.json()["telefono"], "22123456")
        self.assertEqual(self.client.delete(f"{URL}{proveedor_id}/").status_code, 204)
        self.assertFalse(ProveedorModel.objects.filter(pk=proveedor_id).exists())

    def test_buscar_por_nombre(self):
        self._crear(nombre="Ferretera Andina")
        self._crear(nombre="Herramientas del Sur")
        respuesta = self.client.get(URL, {"buscar": "andina"})
        self.assertEqual([p["nombre"] for p in respuesta.json()], ["Ferretera Andina"])

    def test_listar_en_una_sola_consulta(self):
        for i in range(4):
            proveedor = ProveedorModel.objects.create(nombre=f"Prov {i}", telefono="77712345")
            HerramientaModel.objects.create(codigo=f"T-{i}", nombre="X", proveedor=proveedor)
        with self.assertNumQueries(1):
            respuesta = self.client.get(URL)
        self.assertTrue(all(p["cantidad_herramientas"] == 1 for p in respuesta.json()))

    def test_supervisor_y_empleado_consultan_pero_no_escriben(self):
        proveedor_id = self._crear().json()["id"]
        for usuario in (self.supervisor, self.empleado):
            self.client.force_authenticate(usuario)
            self.assertEqual(self.client.get(URL).status_code, 200)
            self.assertEqual(self._crear(nombre="Otro").status_code, 403)
            self.assertEqual(self.client.patch(f"{URL}{proveedor_id}/", {"activo": False}, format="json").status_code, 403)
            self.assertEqual(self.client.delete(f"{URL}{proveedor_id}/").status_code, 403)

    def test_sin_sesion_es_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_validaciones_400(self):
        self._crear()
        duplicado = self._crear(nombre="ferretera andina")
        self.assertEqual(duplicado.status_code, 400)
        self.assertIn("nombre", duplicado.json())
        invalido = self._crear(nombre="Otro", telefono="123", email="x@")
        self.assertEqual(invalido.status_code, 400)
        self.assertEqual(set(invalido.json()), {"telefono", "email"})

    def test_con_herramientas_no_se_elimina_pero_se_desactiva(self):
        proveedor_id = self._crear().json()["id"]
        HerramientaModel.objects.create(codigo="T-1", nombre="Taladro", proveedor_id=proveedor_id)
        respuesta = self.client.delete(f"{URL}{proveedor_id}/")
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("Desactívalo", respuesta.json()["detail"])
        desactivado = self.client.patch(f"{URL}{proveedor_id}/", {"activo": False}, format="json")
        self.assertFalse(desactivado.json()["activo"])

    def test_inexistente_404(self):
        self.assertEqual(self.client.get(f"{URL}9999/").status_code, 404)

    def test_queda_en_el_historial_de_modificaciones(self):
        from apps.auditoria.infrastructure.models import HistorialModificacion
        proveedor_id = self._crear().json()["id"]
        fila = HistorialModificacion.objects.get(tabla_afectada="proveedores.Proveedor", registro_id=str(proveedor_id))
        self.assertEqual((fila.accion, fila.usuario_username), ("INSERT", "admin_test"))


class ProveedorEnCatalogoApiTests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.client.force_authenticate(self.admin)
        self.activo = ProveedorModel.objects.create(nombre="Ferretera Andina", telefono="77712345")
        self.inactivo = ProveedorModel.objects.create(nombre="Cerrada", telefono="77712346", activo=False)

    def _crear(self, **datos):
        return self.client.post(URL_CATALOGO, {"codigo": "T-1", "nombre": "Taladro", **datos}, format="json")

    def test_herramienta_con_proveedor_activo(self):
        respuesta = self._crear(proveedor=self.activo.id)
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual((respuesta.json()["proveedor"], respuesta.json()["proveedor_nombre"]),
                         (self.activo.id, "Ferretera Andina"))

    def test_proveedor_inactivo_o_inexistente_es_400(self):
        for proveedor_id in (self.inactivo.id, 9999):
            with self.subTest(proveedor=proveedor_id):
                respuesta = self._crear(codigo=f"T-{proveedor_id}", proveedor=proveedor_id)
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn("proveedor", respuesta.json())

    def test_herramienta_conserva_su_proveedor_si_luego_se_desactiva(self):
        herramienta_id = self._crear(proveedor=self.activo.id).json()["id"]
        self.client.patch(f"{URL}{self.activo.id}/", {"activo": False}, format="json")
        respuesta = self.client.patch(f"{URL_CATALOGO}{herramienta_id}/", {"nombre": "Taladro 2"}, format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["proveedor"], self.activo.id)

    def test_quitar_el_proveedor(self):
        herramienta_id = self._crear(proveedor=self.activo.id).json()["id"]
        respuesta = self.client.patch(f"{URL_CATALOGO}{herramienta_id}/", {"proveedor": None}, format="json")
        self.assertIsNone(respuesta.json()["proveedor"])

    def test_catalogo_con_proveedores_en_una_sola_consulta(self):
        for i in range(4):
            HerramientaModel.objects.create(codigo=f"H-{i}", nombre="X", proveedor=self.activo)
        with self.assertNumQueries(1):
            self.client.get(URL_CATALOGO)
