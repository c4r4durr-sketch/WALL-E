from rest_framework.routers import DefaultRouter

from .views import HerramientaViewSet

router = DefaultRouter()
router.register("herramientas", HerramientaViewSet, basename="herramienta")

urlpatterns = router.urls
