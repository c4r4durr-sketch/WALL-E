"""
Pruebas de la regla HU5 (sucursal obligatoria para Supervisor y Empleado),
tanto la función pura del dominio como su aplicación en la API, y de la
validación de contraseñas (AUTH_PASSWORD_VALIDATORS) al crear y editar.

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
