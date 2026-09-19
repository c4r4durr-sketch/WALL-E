"""
URLs raíz. Solo cablea: admin de Django, login/refresh JWT, documentación
OpenAPI/Swagger, y un prefijo /api/<bounded-context>/ por app. Cada app es
dueña de sus propias rutas (interfaces/api/urls.py); acá no se define
ninguna vista, solo se incluyen.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.usuarios.interfaces.api.views import CustomTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth JWT
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Documentación (Swagger)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Un prefijo por bounded context
    path("api/usuarios/", include("apps.usuarios.interfaces.api.urls")),
    path("api/catalogo/", include("apps.catalogo.interfaces.api.urls")),
    path("api/movimientos/", include("apps.movimientos.interfaces.api.urls")),
    path("api/transferencias/", include("apps.transferencias.interfaces.api.urls")),
    path("api/indicadores/", include("apps.indicadores.interfaces.api.urls")),
]
