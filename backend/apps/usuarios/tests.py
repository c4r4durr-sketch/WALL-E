"""
Pruebas de la regla HU5 (sucursal obligatoria para Supervisor y Empleado),
tanto la función pura del dominio como su aplicación en la API, y de la
validación de contraseñas (AUTH_PASSWORD_VALIDATORS) al crear y editar, y
de los casos de uso de cuentas (HU3: listar, desactivar, restablecer la
contraseña), con repositorios falsos y contra la API.

Correr con: python manage.py test apps.usuarios
"""

import re

from django.test import SimpleTestCase
from django.urls import URLResolver, get_resolver
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
        payload = {"username": "nuevo", "password": "Clave-Segura-123", "first_name": "Nuevo",
                   "last_name": "Usuario", **datos}
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
        payload = {"username": "nuevo", "password": password, "rol": "ADMINISTRADOR",
                   "first_name": "Nuevo", "last_name": "Usuario", **datos}
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
        datos = {"nombres": "Luis", "apellidos": "Rojas", **datos}
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


class TodasLasVistasExigenSesionTests(APITestCase):
    """Revisión de seguridad: sin token, toda ruta de /api/ responde 401
    para cualquier método. Las únicas públicas son el login y la
    renovación del token (y la documentación, solo con DEBUG)."""

    PUBLICAS = {"api/token/", "api/token/refresh/", "api/schema/", "api/docs/"}

    def _rutas(self, patrones, prefijo=""):
        for patron in patrones:
            ruta = prefijo + str(patron.pattern)
            if isinstance(patron, URLResolver):
                yield from self._rutas(patron.url_patterns, ruta)
            else:
                yield ruta

    def test_sin_token_todo_es_401(self):
        revisadas = 0
        for ruta in self._rutas(get_resolver().url_patterns):
            # Las variantes con sufijo de formato (.json) son la misma vista.
            if not ruta.startswith("api/") or ruta in self.PUBLICAS or "format" in ruta:
                continue
            # <int:pk>, (?P<pk>[^/.]+), formatos .json... -> valores de ejemplo
            url = "/" + re.sub(r"<[^>]+>|\(\?P<[^>]+>[^)]+\)", "1", ruta)
            url = url.replace("^", "").replace("$", "")
            for metodo in ("get", "post", "put", "patch", "delete"):
                respuesta = getattr(self.client, metodo)(url)
                self.assertEqual(respuesta.status_code, 401, f"{metodo.upper()} {url}")
            revisadas += 1
        self.assertGreater(revisadas, 20)


# --- Validación de formularios: Nueva cuenta, Editar cuenta, Restablecer ---


class ValidacionCuentasApiTests(APITestCase):
    """Cada regla de formato da 400 con el mensaje junto a su campo, aunque
    alguien se salte el frontend y llame a la API directo."""

    def setUp(self):
        self.central = Sucursal.objects.create(nombre="Central")
        self.admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.client.force_authenticate(self.admin)

    def _crear(self, **datos):
        payload = {"username": "luis.rojas", "password": "Clave-Segura-123", "first_name": "Luis",
                   "last_name": "Rojas", "rol": "ADMINISTRADOR", **datos}
        return self.client.post(URL_USUARIOS, payload, format="json")

    def _error(self, respuesta, campo):
        self.assertEqual(respuesta.status_code, 400, respuesta.content)
        self.assertIn(campo, respuesta.json())
        return " ".join(respuesta.json()[campo])

    def test_cuenta_valida_ok_y_normaliza_espacios(self):
        respuesta = self._crear(first_name="  María   José ", last_name="O'Brien-Núñez")
        self.assertEqual(respuesta.status_code, 201, respuesta.content)
        self.assertEqual((respuesta.json()["first_name"], respuesta.json()["last_name"]),
                         ("María José", "O'Brien-Núñez"))

    def test_nombre_con_numeros_o_simbolos_es_400(self):
        for nombre in ("Luis2", "Luis!", "L"):
            with self.subTest(nombre=nombre):
                self._error(self._crear(first_name=nombre), "first_name")

    def test_nombre_o_apellido_vacios_o_solo_espacios_son_400(self):
        self.assertIn("obligatorio", self._error(self._crear(first_name="   "), "first_name"))
        self._error(self._crear(last_name=""), "last_name")

    def test_nombre_de_mas_de_50_caracteres_es_400(self):
        self._error(self._crear(last_name="a" * 51), "last_name")

    def test_usuario_invalido_es_400(self):
        for username in ("ab", "luis rojas", "josé", "luis@rojas", "x" * 31):
            with self.subTest(username=username):
                self._error(self._crear(username=username), "username")

    def test_usuario_repetido_es_400(self):
        self._crear()
        self.assertIn("Ya existe", self._error(self._crear(username="LUIS.ROJAS"), "username"))

    def test_correo_invalido_es_400(self):
        self._error(self._crear(email="no-es-correo"), "email")

    def test_password_debil_es_400(self):
        for password in ("clave-segura-123", "ClaveSegura123", "Clave-Segura", "Ab1-"):
            with self.subTest(password=password):
                self._error(self._crear(password=password), "password")

    def test_password_parecida_al_usuario_es_400(self):
        self._error(self._crear(username="rodrigo.perez", password="Rodrigo.Perez1"), "password")

    def test_responde_todos_los_errores_juntos(self):
        respuesta = self._crear(first_name="Luis2", password="debil")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual({"first_name", "password"} - set(respuesta.json()), set())

    def test_editar_nombre_con_numeros_es_400(self):
        cuenta = Usuario.objects.create_user("ana.p", password="x", rol="EMPLEADO", sucursal=self.central,
                                             first_name="Ana", last_name="Paz")
        respuesta = self.client.patch(f"{URL_USUARIOS}{cuenta.id}/", {"first_name": "Ana3"}, format="json")
        self._error(respuesta, "first_name")

    def test_editar_cuenta_antigua_sin_tocar_usuario_ni_nombres_ok(self):
        # Creada antes de las reglas: usuario con "@" y sin nombre. Se puede
        # seguir editando lo demás (el usuario no se edita desde la pantalla).
        antigua = Usuario.objects.create_user("vieja@cuenta", password="x", rol="EMPLEADO", sucursal=self.central)
        respuesta = self.client.patch(f"{URL_USUARIOS}{antigua.id}/", {"email": "v@walle.bo"}, format="json")
        self.assertEqual(respuesta.status_code, 200, respuesta.content)

    def test_restablecer_con_password_sin_simbolo_es_400(self):
        cuenta = Usuario.objects.create_user("ana.p", password="x", rol="ADMINISTRADOR")
        respuesta = self.client.post(f"{URL_USUARIOS}{cuenta.id}/restablecer-password/",
                                     {"password": "ClaveNueva789"}, format="json")
        self.assertIn("símbolo", self._error(respuesta, "password"))
