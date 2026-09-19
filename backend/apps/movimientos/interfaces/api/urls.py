from rest_framework.routers import DefaultRouter

from .views import MovimientoViewSet

router = DefaultRouter()
router.register("", MovimientoViewSet, basename="movimiento")

urlpatterns = router.urls
