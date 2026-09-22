"""
Pruebas de las fórmulas puras de indicadores. Usan SimpleTestCase (sin
base de datos) porque domain/formulas.py no depende de Django ni del ORM.

Correr con: python manage.py test apps.indicadores
"""

from django.test import SimpleTestCase

from .domain.formulas import (
    ajustar_a_cajas,
    cajas_a_unidades,
    calcular_eoq,
    calcular_rop,
    unidades_a_cajas,
)


class CalcularEOQTests(SimpleTestCase):
    def test_formula_basica(self):
        # raiz(2 * 1000 * 50 / 2) = raiz(50000) = 223.606...
        self.assertAlmostEqual(calcular_eoq(1000, 50, 2), 223.6068, places=4)

    def test_sin_costo_almacenamiento_devuelve_none(self):
        self.assertIsNone(calcular_eoq(1000, 50, 0))
        self.assertIsNone(calcular_eoq(1000, 50, None))

    def test_dato_faltante_devuelve_none(self):
        self.assertIsNone(calcular_eoq(None, 50, 2))
        self.assertIsNone(calcular_eoq(1000, None, 2))

    def test_demanda_negativa_es_error(self):
        with self.assertRaises(ValueError):
            calcular_eoq(-1, 50, 2)


class CalcularROPTests(SimpleTestCase):
    def test_formula_basica(self):
        # (730 / 365) * 10 = 20
        self.assertAlmostEqual(calcular_rop(730, 10), 20.0)

    def test_dato_faltante_devuelve_none(self):
        self.assertIsNone(calcular_rop(730, None))
        self.assertIsNone(calcular_rop(None, 10))

    def test_negativo_es_error(self):
        with self.assertRaises(ValueError):
            calcular_rop(730, -1)


class ConversionCajaUnidadTests(SimpleTestCase):
    def test_ajustar_a_cajas_redondea_hacia_arriba(self):
        self.assertEqual(ajustar_a_cajas(30, 12), 36)
        self.assertEqual(ajustar_a_cajas(24, 12), 24)
        self.assertEqual(ajustar_a_cajas(223.6, 12), 228)

    def test_ajustar_a_cajas_sin_factor_valido(self):
        self.assertEqual(ajustar_a_cajas(30, None), 30)
        self.assertEqual(ajustar_a_cajas(30, 0), 30)

    def test_cajas_a_unidades(self):
        self.assertEqual(cajas_a_unidades(3, 12), 36)
        with self.assertRaises(ValueError):
            cajas_a_unidades(3, 0)

    def test_unidades_a_cajas(self):
        self.assertEqual(unidades_a_cajas(30, 12), (2, 6))
        with self.assertRaises(ValueError):
            unidades_a_cajas(-1, 12)
