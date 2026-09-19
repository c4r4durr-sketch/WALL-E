from rest_framework.routers import DefaultRouter

from .views import TransferenciaViewSet

router = DefaultRouter()
router.register("", TransferenciaViewSet, basename="transferencia")

urlpatterns = router.urls
