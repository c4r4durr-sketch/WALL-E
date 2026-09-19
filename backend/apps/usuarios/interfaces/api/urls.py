from rest_framework.routers import DefaultRouter

from .views import SucursalViewSet, UsuarioViewSet

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuario")
router.register("sucursales", SucursalViewSet, basename="sucursal")

urlpatterns = router.urls
