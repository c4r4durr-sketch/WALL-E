"""
Pruebas de la API del catálogo: campos de EOQ/ROP (opcionales) y sus
validaciones.

Correr con: python manage.py test apps.catalogo
"""

from rest_framework.test import APITestCase

from apps.usuarios.infrastructure.models import Usuario

URL = "/api/catalogo/herramientas/"


class HerramientaCamposEOQTests(APITestCase):
    def setUp(self):
        usuario = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.client.force_authenticate(usuario)

    def test_crear_sin_campos_eoq_sigue_funcionando(self):
        respuesta = self.client.post(URL, {"codigo": "T-1", "nombre": "Taladro"}, format="json")
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        for campo in ["demanda_anual", "costo_pedido", "costo_almacenamiento_unitario", "tiempo_entrega_dias"]:
            self.assertIsNone(datos[campo])

    def test_crear_con_campos_eoq_devuelve_numeros(self):
        respuesta = self.client.post(
            URL,
            {
                "codigo": "T-2",
                "nombre": "Amoladora",
                "unidades_por_caja": 12,
                "demanda_anual": 1000,
                "costo_pedido": "50.00",
                "costo_almacenamiento_unitario": 2.5,
                "tiempo_entrega_dias": 10,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertEqual(datos["demanda_anual"], 1000)
        self.assertEqual(datos["costo_pedido"], 50)
        self.assertEqual(datos["costo_almacenamiento_unitario"], 2.5)
        self.assertEqual(datos["tiempo_entrega_dias"], 10)

    def test_valores_negativos_son_400(self):
        for campo in ["demanda_anual", "costo_pedido", "costo_almacenamiento_unitario", "tiempo_entrega_dias"]:
            with self.subTest(campo=campo):
                respuesta = self.client.post(
                    URL, {"codigo": f"N-{campo}", "nombre": "x", campo: -1}, format="json"
                )
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.json())

    def test_unidades_por_caja_cero_es_400(self):
        respuesta = self.client.post(
            URL, {"codigo": "C-0", "nombre": "x", "unidades_por_caja": 0}, format="json"
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("unidades_por_caja", respuesta.json())
