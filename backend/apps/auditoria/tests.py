"""
Pruebas del historial de modificaciones (HU13):
  - consulta con un repositorio falso (permisos, filtros, paginación,
    campos cambiados);
  - la API real: los cambios hechos por la API quedan registrados y se
    consultan con filtros; la contraseña nunca aparece; solo lectura.

Correr con: python manage.py test apps.auditoria
"""

from datetime import date, datetime, time, timedelta

from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.catalogo.tests import MediaTemporal, imagen_de_prueba

from apps.usuarios.domain.entities import Actor
from apps.usuarios.domain.value_objects import Rol
from apps.usuarios.infrastructure.models import Sucursal, Usuario

from .domain.entities import FiltroHistorial, OpcionFiltro, RegistroHistorial
from .domain.exceptions import ConsultaNoPermitidaError, FiltroInvalidoError
from .domain.repositories import HistorialRepository
from .domain.value_objects import AccionAuditoria
from .infrastructure.models import HistorialModificacion
from .use_cases import consultar_historial as casos

URL = "/api/auditoria/historial/"
ADMIN = Actor(usuario_id=1, rol=Rol.ADMINISTRADOR, sucursal_id=None)
SUPERVISOR = Actor(usuario_id=2, rol=Rol.SUPERVISOR, sucursal_id=1)
EMPLEADO = Actor(usuario_id=3, rol=Rol.EMPLEADO, sucursal_id=1)


def _registro(id, accion=AccionAuditoria.UPDATE, antes=None, despues=None):
    return RegistroHistorial(
        id=id, fecha=datetime(2026, 10, 20, 10, 0), tabla="catalogo.Herramienta", tabla_nombre="Herramientas",
        registro_id="1", accion=accion, usuario_id=1, usuario_username="admin",
        datos_anteriores=antes, datos_nuevos=despues,
    )


class _HistorialFalso(HistorialRepository):
    def __init__(self, registros):
        self.registros = registros
        self.pedido = None

    def buscar(self, filtro, desde, limite):
        self.pedido = (filtro, desde, limite)
        return len(self.registros), self.registros[desde:desde + limite]

    def tablas(self):
        return [OpcionFiltro("catalogo.Herramienta", "Herramientas")]

    def autores(self):
        return [OpcionFiltro("1", "admin")]


class ConsultarHistorialTests(SimpleTestCase):
    def test_campos_cambiados_solo_en_ediciones(self):
        edicion = _registro(1, antes={"nombre": "A", "codigo": "T", "costo": 1, "actualizado_en": "x"},
                            despues={"nombre": "B", "codigo": "T", "costo": 2, "actualizado_en": "y"})
        self.assertEqual(casos.campos_cambiados(edicion), ("costo", "nombre"))
        alta = _registro(2, AccionAuditoria.INSERT, despues={"nombre": "A"})
        self.assertEqual(casos.campos_cambiados(alta), ())

    def test_empleado_no_consulta(self):
        repo = _HistorialFalso([])
        with self.assertRaises(ConsultaNoPermitidaError):
            casos.consultar_historial(repo, EMPLEADO, FiltroHistorial())
        with self.assertRaises(ConsultaNoPermitidaError):
            casos.opciones_de_filtro(repo, EMPLEADO)
        casos.consultar_historial(repo, SUPERVISOR, FiltroHistorial())

    def test_desde_posterior_a_hasta(self):
        with self.assertRaises(FiltroInvalidoError):
            casos.consultar_historial(
                _HistorialFalso([]), ADMIN, FiltroHistorial(desde=date(2026, 10, 20), hasta=date(2026, 10, 1))
            )

    def test_paginacion(self):
        repo = _HistorialFalso([_registro(i) for i in range(1, 8)])
        pagina = casos.consultar_historial(repo, ADMIN, FiltroHistorial(), pagina=2, tamano=3)
        self.assertEqual(([r.id for r in pagina.resultados], pagina.total, pagina.paginas), ([4, 5, 6], 7, 3))
        casos.consultar_historial(repo, ADMIN, FiltroHistorial(), pagina=0, tamano=1000)
        self.assertEqual(repo.pedido[1:], (0, casos.TAMANO_MAXIMO))

    def test_opciones_con_acciones_en_espanol(self):
        opciones = casos.opciones_de_filtro(_HistorialFalso([]), ADMIN)
        self.assertEqual([a.texto for a in opciones["acciones"]], ["Alta", "Edición", "Baja"])


class HistorialApiTests(MediaTemporal, APITestCase):
    def setUp(self):
        self.central = Sucursal.objects.create(nombre="Central")
        self.admin = Usuario.objects.create_user("admin_test", password="x", rol="ADMINISTRADOR")
        self.sup = Usuario.objects.create_user("sup", password="x", rol="SUPERVISOR", sucursal=self.central)
        self.emp = Usuario.objects.create_user("emp", password="x", rol="EMPLEADO", sucursal=self.central)
        # Cambios reales hechos por la API: quedan en el historial con autor.
        self.client.force_authenticate(self.admin)
        self.herramienta_id = self.client.post(
            "/api/catalogo/herramientas/", {"codigo": "T-1", "nombre": "Taladro", "imagen": imagen_de_prueba()},
            format="multipart",
        ).json()["id"]
        self.client.patch(f"/api/catalogo/herramientas/{self.herramienta_id}/", {"nombre": "Taladro grande"}, format="json")
        self.client.post(f"/api/usuarios/usuarios/{self.emp.id}/restablecer-password/",
                         {"password": "Nueva-Clave-789"}, format="json")

    def test_admin_y_supervisor_consultan_con_autor_y_cambios(self):
        for usuario in (self.admin, self.sup):
            self.client.force_authenticate(usuario)
            respuesta = self.client.get(URL, {"tabla": "catalogo.Herramienta"})
            self.assertEqual(respuesta.status_code, 200)
            datos = respuesta.json()
            self.assertEqual(datos["total"], 2)
            edicion, alta = datos["resultados"]  # del más reciente al más antiguo
            self.assertEqual((edicion["accion"], edicion["usuario"], edicion["tabla_nombre"]),
                             ("UPDATE", "admin_test", "Herramientas"))
            self.assertEqual(edicion["campos_cambiados"], ["nombre"])
            self.assertEqual((edicion["datos_anteriores"]["nombre"], edicion["datos_nuevos"]["nombre"]),
                             ("Taladro", "Taladro grande"))
            self.assertEqual(alta["accion"], "INSERT")

    def test_empleado_403_y_sin_sesion_401(self):
        self.client.force_authenticate(self.emp)
        self.assertEqual(self.client.get(URL).status_code, 403)
        self.assertEqual(self.client.get(f"{URL}opciones/").status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(URL).status_code, 401)

    def test_solo_lectura(self):
        self.assertEqual(self.client.post(URL, {}, format="json").status_code, 405)
        self.assertEqual(self.client.delete(URL).status_code, 405)

    def test_la_password_nunca_aparece(self):
        datos = self.client.get(URL, {"tabla": "usuarios.Usuario", "tamano": 100}).json()
        self.assertGreater(datos["total"], 0)
        for registro in datos["resultados"]:
            self.assertNotIn("password", registro["datos_anteriores"] or {})
            self.assertNotIn("password", registro["datos_nuevos"] or {})

    def test_filtros_por_usuario_y_accion(self):
        sin_autor = HistorialModificacion.objects.filter(usuario__isnull=True).count()
        por_admin = self.client.get(URL, {"usuario": self.admin.id}).json()
        self.assertEqual(por_admin["total"], HistorialModificacion.objects.count() - sin_autor)
        altas = self.client.get(URL, {"accion": "INSERT", "tabla": "catalogo.Herramienta"}).json()
        self.assertEqual(altas["total"], 1)

    def test_filtro_por_dia_de_la_paz(self):
        la_paz = timezone.get_current_timezone()
        ayer = timezone.localdate() - timedelta(days=1)
        # 23:30 de ayer en La Paz = 03:30 UTC de hoy: cuenta como AYER.
        fila = HistorialModificacion.objects.filter(accion="INSERT", tabla_afectada="catalogo.Herramienta").get()
        HistorialModificacion.objects.filter(pk=fila.pk).update(
            fecha=datetime.combine(ayer, time(23, 30), tzinfo=la_paz)
        )
        datos = self.client.get(URL, {"desde": ayer.isoformat(), "hasta": ayer.isoformat()}).json()
        self.assertEqual([r["id"] for r in datos["resultados"]], [fila.pk])

    def test_validaciones_400(self):
        self.assertEqual(self.client.get(URL, {"desde": "2026-10-20", "hasta": "2026-10-01"}).status_code, 400)
        self.assertEqual(self.client.get(URL, {"accion": "BORRAR"}).status_code, 400)
        self.assertEqual(self.client.get(URL, {"tamano": 500}).status_code, 400)

    def test_paginacion_y_consultas_constantes(self):
        for i in range(30):
            HistorialModificacion.objects.create(tabla_afectada="catalogo.Herramienta", registro_id=str(i),
                                                 accion="UPDATE", usuario=self.admin, usuario_username="admin_test")
        with self.assertNumQueries(2):  # COUNT + página
            datos = self.client.get(URL, {"pagina": 2, "tamano": 10}).json()
        self.assertEqual((datos["pagina"], datos["tamano"], len(datos["resultados"])), (2, 10, 10))
        self.assertEqual(datos["paginas"], -(-datos["total"] // 10))

    def test_opciones(self):
        datos = self.client.get(f"{URL}opciones/").json()
        tablas = {t["valor"]: t["texto"] for t in datos["tablas"]}
        self.assertEqual(tablas["catalogo.Herramienta"], "Herramientas")
        self.assertIn({"valor": str(self.admin.id), "texto": "admin_test"}, datos["usuarios"])
        self.assertEqual([a["valor"] for a in datos["acciones"]], ["INSERT", "UPDATE", "DELETE"])

    def test_filtro_por_origen_separa_los_comandos(self):
        from apps.auditoria.infrastructure.contexto import registrar_como
        # Un comando sin nombre (consola) y cargar_demo, que firma lo suyo.
        HistorialModificacion.objects.create(tabla_afectada="usuarios.Sucursal", registro_id="1", accion="UPDATE")
        with registrar_como("cargar_demo"):
            Sucursal.objects.create(nombre="Norte")
        demo = HistorialModificacion.objects.get(tabla_afectada="usuarios.Sucursal", accion="INSERT",
                                                 registro_id=str(Sucursal.objects.get(nombre="Norte").pk))
        self.assertEqual((demo.usuario_id, demo.usuario_username), (None, "cargar_demo"))
        # Un usuario borrado conserva su nombre: sigue siendo de usuarios.
        HistorialModificacion.objects.create(tabla_afectada="usuarios.Sucursal", registro_id="2", accion="UPDATE",
                                             usuario_username="ex_empleado")

        comandos = self.client.get(URL, {"origen": "COMANDOS"}).json()
        self.assertTrue(all(r["usuario_id"] is None and r["usuario"] in ("", "cargar_demo")
                            for r in comandos["resultados"]))
        self.assertIn("cargar_demo", [r["usuario"] for r in comandos["resultados"]])
        usuarios = self.client.get(URL, {"origen": "USUARIOS"}).json()
        self.assertNotIn("cargar_demo", [r["usuario"] for r in usuarios["resultados"]])
        self.assertIn("ex_empleado", [r["usuario"] for r in usuarios["resultados"]])
        self.assertEqual(comandos["total"] + usuarios["total"], HistorialModificacion.objects.count())
        self.assertEqual(self.client.get(URL, {"origen": "OTRO"}).status_code, 400)
        opciones = self.client.get(f"{URL}opciones/").json()["origenes"]
        self.assertEqual([o["valor"] for o in opciones], ["USUARIOS", "COMANDOS"])
