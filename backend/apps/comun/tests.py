"""
Pruebas de las reglas de formato compartidas (apps/comun/reglas.py), del
validador propio de contraseñas y de los campos estrictos de DRF
(apps/comun/campos.py). Las pruebas de cada formulario contra la API
están en el tests.py de su módulo.

Correr con: python manage.py test apps.comun
"""

from decimal import Decimal

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from rest_framework import serializers

from apps.usuarios.infrastructure.models import Usuario

from . import reglas
from .campos import EnteroEstricto, Monto


class NombrePersonaTests(SimpleTestCase):
    def test_validos(self):
        for nombre in ("Ana", "María José", "Núñez", "O'Brien", "Pérez-Gómez", "Lü"):
            with self.subTest(nombre=nombre):
                self.assertIsNone(reglas.error_nombre_persona(nombre))

    def test_invalidos(self):
        for nombre in ("", "A", "Ana2", "Ana_", "Ana!", "J.", "-Ana", "Ana--Paz", "x" * 51):
            with self.subTest(nombre=nombre):
                self.assertIsNotNone(reglas.error_nombre_persona(nombre))

    def test_normalizar_quita_espacios_y_solo_espacios_queda_vacio(self):
        self.assertEqual(reglas.normalizar_espacios("  María   José "), "María José")
        self.assertEqual(reglas.normalizar_espacios("    "), "")
        self.assertIn("obligatorio", reglas.error_nombre_persona(reglas.normalizar_espacios("   ")))


class UsernameTests(SimpleTestCase):
    def test_validos(self):
        for username in ("ana", "ana.perez", "ana_p-2", "A1b"):
            with self.subTest(username=username):
                self.assertIsNone(reglas.error_username(username))

    def test_invalidos(self):
        for username in ("", "ab", "ana perez", "ana@x", "josé", "x" * 31, "ana+1"):
            with self.subTest(username=username):
                self.assertIsNotNone(reglas.error_username(username))


class TelefonoTests(SimpleTestCase):
    def test_validos(self):
        for telefono in ("7771234", "+591 2 2456789", "777-12345", "123456789012345"):
            with self.subTest(telefono=telefono):
                self.assertIsNone(reglas.error_telefono(telefono))

    def test_invalidos(self):
        for telefono in ("", "123456", "1234567890123456", "(2) 2123456", "77a12345", "591+7771234"):
            with self.subTest(telefono=telefono):
                self.assertIsNotNone(reglas.error_telefono(telefono))


class CodigoTests(SimpleTestCase):
    def test_normaliza_a_mayusculas(self):
        self.assertEqual(reglas.normalizar_codigo("  tal-18v "), "TAL-18V")

    def test_validos_e_invalidos(self):
        for codigo in ("T-1", "TAL18V", "SIE-CIR-2"):
            with self.subTest(codigo=codigo):
                self.assertIsNone(reglas.error_codigo(codigo))
        for codigo in ("", "T 1", "T_1", "-T1", "T--1", "T1-", "Ñ-1", "X" * 31):
            with self.subTest(codigo=codigo):
                self.assertIsNotNone(reglas.error_codigo(codigo))


class TextoTests(SimpleTestCase):
    def test_obligatorio_y_largo_maximo(self):
        self.assertIsNotNone(reglas.error_texto("", "El motivo", obligatorio=True))
        self.assertIsNone(reglas.error_texto("", "El motivo", obligatorio=False))
        self.assertIsNotNone(reglas.error_texto("x" * 256, "El motivo", obligatorio=False))
        self.assertIsNone(reglas.error_texto("x" * 255, "El motivo", obligatorio=True))


class PoliticaPasswordTests(SimpleTestCase):
    """La política completa de AUTH_PASSWORD_VALIDATORS: la de Django más
    ComplejidadPasswordValidator. Es la misma que muestra la barra de
    seguridad del frontend."""

    def _errores(self, password, **datos):
        usuario = Usuario(username=datos.get("username", "cuenta"), first_name=datos.get("first_name", ""))
        try:
            validate_password(password, user=usuario)
        except ValidationError as error:
            return error.messages
        return []

    def test_cumple_la_politica(self):
        self.assertEqual(self._errores("Clave-Segura-123"), [])

    def test_le_falta_cada_requisito(self):
        for password, falta in [
            ("clave-segura-123", "mayúscula"),
            ("CLAVE-SEGURA-123", "minúscula"),
            ("Clave-Segura", "número"),
            ("ClaveSegura123", "símbolo"),
        ]:
            with self.subTest(password=password):
                self.assertIn(falta, " ".join(self._errores(password)))

    def test_corta_y_parecida_al_usuario(self):
        self.assertIn("8", " ".join(self._errores("Ab1-")))
        self.assertTrue(self._errores("Rodrigo.Perez1", username="rodrigo.perez1"))

    def test_faltantes_es_la_regla_pura(self):
        self.assertEqual(reglas.faltantes_password("abc"), ["una mayúscula", "un número", "un símbolo"])
        self.assertEqual(reglas.faltantes_password("Ab1!"), [])


class _Forma(serializers.Serializer):
    cantidad = EnteroEstricto(min_value=1)
    monto = Monto(required=False, allow_null=True)


class CamposEstrictosTests(SimpleTestCase):
    def _valida(self, **datos):
        forma = _Forma(data={"cantidad": 1, **datos})
        return forma.is_valid(), forma.errors

    def test_entero_acepta_enteros_y_su_texto(self):
        for valor in (5, "5", " 7 "):
            with self.subTest(valor=valor):
                self.assertTrue(self._valida(cantidad=valor)[0])

    def test_entero_rechaza_decimales_negativos_e_y_booleanos(self):
        for valor in (2.5, 2.0, "2.0", "2,5", "1e3", 1e3, -3, "-3", 0, True, "", "abc"):
            with self.subTest(valor=valor):
                valido, errores = self._valida(cantidad=valor)
                self.assertFalse(valido)
                self.assertIn("cantidad", errores)

    def test_monto_mayor_que_cero_con_dos_decimales(self):
        valido, _ = self._valida(monto="12.50")
        self.assertTrue(valido)
        self.assertEqual(_Forma(data={"cantidad": 1, "monto": "0.01"}).is_valid(), True)
        for valor in ("0", 0, "-1", "1.234", "1e3", "abc"):
            with self.subTest(valor=valor):
                self.assertFalse(self._valida(monto=valor)[0])

    def test_monto_devuelve_decimal(self):
        forma = _Forma(data={"cantidad": 1, "monto": "3.5"})
        forma.is_valid()
        self.assertEqual(forma.validated_data["monto"], Decimal("3.50"))
