"""
Pruebas de la regla HU5 (sucursal obligatoria para Supervisor y Empleado),
tanto la función pura del dominio como su aplicación en la API.

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
