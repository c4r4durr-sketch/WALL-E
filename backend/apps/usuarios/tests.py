"""
Pruebas de la regla HU5 (sucursal obligatoria para Supervisor y Empleado),
tanto la función pura del dominio como su aplicación en la API, y de la
validación de contraseñas (AUTH_PASSWORD_VALIDATORS) al crear y editar, y
de los casos de uso de cuentas (HU3: listar, desactivar, restablecer la
contraseña), con repositorios falsos y contra la API.

Correr con: python manage.py test apps.usuarios
"""

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from .domain.reglas import requiere_sucursal
from .infrastructure.models import Sucursal, Usuario

URL_USUARIOS = "/api/usuarios/usuarios/"


class RequiereSucursalTests(SimpleTestCase):
    def test_por_rol(self):
        self.assertFalse(requiere_sucursal("ADMINISTRADOR"))
        self.assertTrue(requiere_sucursal("SUPERVISOR"))
        self.assertTrue(requiere_sucursal("EMPLEADO"))


class SucursalObligatoriaApiTests(APITestCase):
    def setUp(self):
        self.sucursal = Sucursal.objects.create(nombre="Central")
        admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.client.force_authenticate(admin)

    def _crear(self, **datos):
        payload = {"username": "nuevo", "password": "Clave-Segura-123", **datos}
        return self.client.post(URL_USUARIOS, payload, format="json")

    def test_crear_empleado_sin_sucursal_es_400(self):
        respuesta = self._crear(rol="EMPLEADO")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("sucursal", respuesta.json())

    def test_crear_supervisor_con_sucursal_null_es_400(self):
        respuesta = self._crear(rol="SUPERVISOR", sucursal=None)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("sucursal", respuesta.json())

    def test_crear_empleado_con_sucursal_ok(self):
        respuesta = self._crear(rol="EMPLEADO", sucursal=self.sucursal.id)
        self.assertEqual(respuesta.status_code, 201)

    def test_crear_administrador_sin_sucursal_ok(self):
        respuesta = self._crear(rol="ADMINISTRADOR")
        self.assertEqual(respuesta.status_code, 201)

    def test_editar_quitando_sucursal_es_400(self):
        empleado = Usuario.objects.create_user(
            "emp", password="x", rol="EMPLEADO", sucursal=self.sucursal
        )
        respuesta = self.client.patch(
            f"{URL_USUARIOS}{empleado.id}/", {"sucursal": None}, format="json"
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_editar_admin_a_empleado_sin_sucursal_es_400(self):
        # El PATCH solo manda el rol: la validación debe usar la sucursal
        # actual del usuario (None) y rechazarlo.
        otro_admin = Usuario.objects.create_user("adm2", password="x", rol="ADMINISTRADOR")
        respuesta = self.client.patch(
            f"{URL_USUARIOS}{otro_admin.id}/", {"rol": "EMPLEADO"}, format="json"
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_editar_otro_campo_de_empleado_valido_ok(self):
        empleado = Usuario.objects.create_user(
            "emp2", password="x", rol="EMPLEADO", sucursal=self.sucursal
        )
        respuesta = self.client.patch(
            f"{URL_USUARIOS}{empleado.id}/", {"first_name": "Ana"}, format="json"
        )
        self.assertEqual(respuesta.status_code, 200)


class ValidacionPasswordApiTests(APITestCase):
    def setUp(self):
        admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.client.force_authenticate(admin)

    def _crear(self, password, **datos):
        payload = {"username": "nuevo", "password": password, "rol": "ADMINISTRADOR", **datos}
        return self.client.post(URL_USUARIOS, payload, format="json")

    def test_crear_con_password_corta_es_400_en_espanol(self):
        respuesta = self._crear("Ab1")
        self.assertEqual(respuesta.status_code, 400)
        mensajes = " ".join(respuesta.json()["password"])
        self.assertIn("contraseña", mensajes)
        self.assertIn("8", mensajes)

    def test_crear_con_password_comun_es_400(self):
        respuesta = self._crear("password123")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("password", respuesta.json())

    def test_crear_con_password_solo_numeros_es_400(self):
        respuesta = self._crear("83920571")
        self.assertEqual(respuesta.status_code, 400)

    def test_crear_con_password_parecida_al_usuario_es_400(self):
        respuesta = self._crear("rodrigo.perez", username="rodrigo.perez")
        self.assertEqual(respuesta.status_code, 400)

    def test_crear_con_password_segura_ok(self):
        respuesta = self._crear("Clave-Segura-123")
        self.assertEqual(respuesta.status_code, 201)
        usuario = Usuario.objects.get(username="nuevo")
        self.assertTrue(usuario.check_password("Clave-Segura-123"))

    def test_editar_con_password_debil_es_400_y_no_la_cambia(self):
        otro = Usuario.objects.create_user("otro", password="Clave-Vieja-456", rol="ADMINISTRADOR")
        respuesta = self.client.patch(
            f"{URL_USUARIOS}{otro.id}/", {"password": "123"}, format="json"
        )
        self.assertEqual(respuesta.status_code, 400)
        otro.refresh_from_db()
        self.assertTrue(otro.check_password("Clave-Vieja-456"))

    def test_editar_con_password_segura_la_cambia(self):
        otro = Usuario.objects.create_user("otro", password="Clave-Vieja-456", rol="ADMINISTRADOR")
        respuesta = self.client.patch(
            f"{URL_USUARIOS}{otro.id}/", {"password": "Clave-Nueva-789"}, format="json"
        )
        self.assertEqual(respuesta.status_code, 200)
        otro.refresh_from_db()
        self.assertTrue(otro.check_password("Clave-Nueva-789"))


# --- Casos de uso con repositorios falsos (sin base de datos) ---

from dataclasses import replace as _replace

from .domain.entities import Actor, Sucursal as SucursalEntidad, Usuario as UsuarioEntidad
from .domain.exceptions import (
    DatosUsuarioInvalidosError,
    OperacionNoPermitidaError,
    PermisoDenegadoError,
    UsernameDuplicadoError,
)
from .domain.repositories import SucursalRepository, UsuarioRepository, ValidadorPassword
from .domain.value_objects import Rol
from .use_cases import gestionar_usuarios as casos


class _UsuariosFalsos(UsuarioRepository):
    def __init__(self, *usuarios):
        self.datos = {u.id: u for u in usuarios}
        self.passwords = {}

    def obtener_por_id(self, usuario_id):
        return self.datos.get(usuario_id)

    def obtener_por_username(self, username):
        return next((u for u in self.datos.values() if u.username.lower() == username.lower()), None)

    def listar(self):
        return list(self.datos.values())

    def crear(self, usuario, password):
        nuevo = _replace(usuario, id=max(self.datos, default=0) + 1)
        self.datos[nuevo.id] = nuevo
        self.passwords[nuevo.id] = password
        return nuevo

    def actualizar(self, usuario):
        self.datos[usuario.id] = usuario
        return usuario

    def establecer_password(self, usuario_id, password):
        self.passwords[usuario_id] = password

    def contar_administradores_activos(self, excluir_id=None):
        return sum(
            1 for u in self.datos.values()
            if u.rol == Rol.ADMINISTRADOR and u.activo and u.id != excluir_id
        )


class _SucursalesFalsas(SucursalRepository):
    def __init__(self):
        self.datos = {1: SucursalEntidad(1, "Central", ""), 2: SucursalEntidad(2, "Cerrada", "", activa=False)}

    def obtener_por_id(self, sucursal_id):
        return self.datos.get(sucursal_id)

    def listar(self):
        return list(self.datos.values())


class _ValidadorFalso(ValidadorPassword):
    def errores(self, password, usuario):
        return [] if len(password) >= 8 else ["Muy corta."]


def _usuario(id, rol=Rol.EMPLEADO, sucursal_id=1, activo=True, username=None):
    return UsuarioEntidad(id=id, username=username or f"u{id}", nombres="", apellidos="",
                          rol=rol, sucursal_id=sucursal_id, activo=activo)


ADMIN = Actor(usuario_id=1, rol=Rol.ADMINISTRADOR, sucursal_id=None)


class GestionarUsuariosTests(SimpleTestCase):
    def setUp(self):
        self.usuarios = _UsuariosFalsos(
            _usuario(1, Rol.ADMINISTRADOR, None, username="admin"),
            _usuario(2, Rol.EMPLEADO, 1, username="ana"),
        )
        self.sucursales = _SucursalesFalsas()
        self.validador = _ValidadorFalso()

    def _crear(self, password="Clave-Segura", **datos):
        return casos.crear_usuario(ADMIN, self.usuarios, self.sucursales, self.validador, datos, password)

    def _editar(self, usuario_id, actor=ADMIN, password=None, **cambios):
        return casos.actualizar_usuario(actor, self.usuarios, self.sucursales, self.validador,
                                        usuario_id, cambios, password)

    def test_solo_el_administrador_gestiona_cuentas(self):
        supervisor = Actor(usuario_id=3, rol=Rol.SUPERVISOR, sucursal_id=1)
        with self.assertRaises(PermisoDenegadoError):
            casos.listar_usuarios(supervisor, self.usuarios)
        with self.assertRaises(PermisoDenegadoError):
            casos.restablecer_password(supervisor, self.usuarios, self.validador, 2, "Clave-Segura")

    def test_crear_normaliza_y_guarda_la_password(self):
        nuevo = self._crear(username="  luis ", nombres=" Luis ", rol=Rol.EMPLEADO, sucursal_id=1)
        self.assertEqual((nuevo.username, nuevo.nombres), ("luis", "Luis"))
        self.assertEqual(self.usuarios.passwords[nuevo.id], "Clave-Segura")

    def test_crear_sin_password_es_invalido(self):
        with self.assertRaises(DatosUsuarioInvalidosError) as ctx:
            self._crear(password=None, username="luis", rol=Rol.ADMINISTRADOR)
        self.assertIn("password", ctx.exception.errores)

    def test_username_duplicado_sin_distinguir_mayusculas(self):
        with self.assertRaises(UsernameDuplicadoError):
            self._crear(username="ANA", rol=Rol.ADMINISTRADOR)

    def test_username_con_espacios_o_corto_es_invalido(self):
        for username in ("ana maria", "ab", ""):
            with self.assertRaises(DatosUsuarioInvalidosError, msg=username):
                self._crear(username=username, rol=Rol.ADMINISTRADOR)

    def test_sucursal_inactiva_o_inexistente_es_invalida(self):
        for sucursal_id in (2, 99):
            with self.assertRaises(DatosUsuarioInvalidosError, msg=sucursal_id):
                self._crear(username="luis", rol=Rol.EMPLEADO, sucursal_id=sucursal_id)

    def test_editar_sin_password_la_conserva(self):
        self.usuarios.passwords[2] = "Vieja-Clave"
        self._editar(2, nombres="Ana")
        self.assertEqual(self.usuarios.passwords[2], "Vieja-Clave")

    def test_pasar_a_administrador_quita_la_sucursal(self):
        self.assertIsNone(self._editar(2, rol=Rol.ADMINISTRADOR).sucursal_id)

    def test_no_puede_desactivarse_ni_quitarse_el_rol_a_si_mismo(self):
        self.usuarios.crear(_usuario(None, Rol.ADMINISTRADOR, None, username="otro"), "x")
        with self.assertRaises(OperacionNoPermitidaError):
            self._editar(1, activo=False)
        with self.assertRaises(OperacionNoPermitidaError):
            self._editar(1, rol=Rol.SUPERVISOR, sucursal_id=1)

    def test_no_se_desactiva_al_ultimo_administrador_activo(self):
        # Caso defensivo: el actor ya no figura como admin activo, y
        # desactivar al único admin activo dejaría el sistema sin admins.
        otro_actor = Actor(usuario_id=99, rol=Rol.ADMINISTRADOR, sucursal_id=None)
        with self.assertRaises(OperacionNoPermitidaError):
            self._editar(1, actor=otro_actor, activo=False)

    def test_desactivar_a_otro_administrador_si_queda_uno(self):
        segundo = self.usuarios.crear(_usuario(None, Rol.ADMINISTRADOR, None, username="otro"), "x")
        self.assertFalse(self._editar(segundo.id, activo=False).activo)

    def test_restablecer_valida_la_politica(self):
        with self.assertRaises(DatosUsuarioInvalidosError):
            casos.restablecer_password(ADMIN, self.usuarios, self.validador, 2, "corta")
        casos.restablecer_password(ADMIN, self.usuarios, self.validador, 2, "Nueva-Clave-1")
        self.assertEqual(self.usuarios.passwords[2], "Nueva-Clave-1")


# --- API de cuentas (HU3) ---


class CuentasApiTests(APITestCase):
    def setUp(self):
        self.central = Sucursal.objects.create(nombre="Central")
        self.admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.empleado = Usuario.objects.create_user(
            "ana", password="Clave-Vieja-456", rol="EMPLEADO", sucursal=self.central
        )
        self.client.force_authenticate(self.admin)

    def _url(self, usuario, sufijo=""):
        return f"{URL_USUARIOS}{usuario.id}/{sufijo}"

    def _restablecer(self, usuario, password="Nueva-Clave-789"):
        return self.client.post(self._url(usuario, "restablecer-password/"), {"password": password}, format="json")

    def test_listar_trae_el_nombre_de_la_sucursal_sin_password(self):
        respuesta = self.client.get(URL_USUARIOS)
        self.assertEqual(respuesta.status_code, 200)
        ana = next(u for u in respuesta.json() if u["username"] == "ana")
        self.assertEqual(ana["sucursal_nombre"], "Central")
        self.assertNotIn("password", ana)

    def test_listar_no_hace_una_consulta_por_usuario(self):
        for i in range(5):
            Usuario.objects.create_user(f"emp{i}", password="x", rol="EMPLEADO", sucursal=self.central)
        with self.assertNumQueries(1):
            self.client.get(URL_USUARIOS)

    def test_supervisor_y_empleado_reciben_403(self):
        supervisor = Usuario.objects.create_user("sup", password="x", rol="SUPERVISOR", sucursal=self.central)
        for usuario in (supervisor, self.empleado):
            self.client.force_authenticate(usuario)
            self.assertEqual(self.client.get(URL_USUARIOS).status_code, 403)
            self.assertEqual(self._restablecer(self.empleado).status_code, 403)

    def test_sin_sesion_es_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(URL_USUARIOS).status_code, 401)

    def test_restablecer_password(self):
        self.assertEqual(self._restablecer(self.empleado).status_code, 204)
        self.empleado.refresh_from_db()
        self.assertTrue(self.empleado.check_password("Nueva-Clave-789"))
        self.assertFalse(self.empleado.check_password("Clave-Vieja-456"))

    def test_restablecer_con_password_debil_es_400(self):
        respuesta = self._restablecer(self.empleado, "123")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("password", respuesta.json())

    def test_restablecer_usuario_inexistente_es_404(self):
        respuesta = self.client.post(
            f"{URL_USUARIOS}9999/restablecer-password/", {"password": "Nueva-Clave-789"}, format="json"
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_la_password_no_queda_en_el_historial(self):
        from apps.auditoria.infrastructure.models import HistorialModificacion
        self._restablecer(self.empleado)
        filas = HistorialModificacion.objects.filter(tabla_afectada="usuarios.Usuario")
        self.assertTrue(filas.exists())
        for fila in filas:
            self.assertNotIn("password", fila.datos_anteriores or {})
            self.assertNotIn("password", fila.datos_nuevos or {})

    def test_desactivar_cuenta_impide_el_login(self):
        respuesta = self.client.patch(self._url(self.empleado), {"is_active": False}, format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()["is_active"])
        login = self.client.post("/api/token/", {"username": "ana", "password": "Clave-Vieja-456"}, format="json")
        self.assertEqual(login.status_code, 401)

    def test_desactivarse_a_si_mismo_es_409(self):
        respuesta = self.client.patch(self._url(self.admin), {"is_active": False}, format="json")
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("detail", respuesta.json())

    def test_username_duplicado_sin_mayusculas_es_400(self):
        respuesta = self.client.post(
            URL_USUARIOS, {"username": "ANA", "password": "Clave-Segura-123", "rol": "ADMINISTRADOR"}, format="json"
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("username", respuesta.json())

    def test_crear_sin_password_es_400(self):
        respuesta = self.client.post(URL_USUARIOS, {"username": "luis", "rol": "ADMINISTRADOR"}, format="json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("password", respuesta.json())

    def test_no_se_eliminan_cuentas(self):
        self.assertEqual(self.client.delete(self._url(self.empleado)).status_code, 405)
        self.assertTrue(Usuario.objects.filter(pk=self.empleado.pk).exists())
