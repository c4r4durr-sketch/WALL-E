"""
Django settings for config project.

Solo configuración de infraestructura (DB, apps instaladas, JWT, CORS,
docs). Ninguna regla de negocio vive acá: eso está en domain/ y use_cases/
de cada app.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# django-environ lee backend/.env y expone os.environ + parseo de tipos
# (bool, list, db-url). Así el proyecto no hardcodea secretos ni credenciales
# de base de datos en el código fuente.
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-change-me-in-.env")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    # Apps propias, una por bounded context. Cada una sigue la misma
    # estructura interna: domain/ use_cases/ infrastructure/ interfaces/api/
    "apps.usuarios.apps.UsuariosConfig",
    "apps.catalogo.apps.CatalogoConfig",
    "apps.movimientos.apps.MovimientosConfig",
    "apps.transferencias.apps.TransferenciasConfig",
    "apps.indicadores.apps.IndicadoresConfig",
    "apps.auditoria.apps.AuditoriaConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CorsMiddleware va antes de CommonMiddleware (requisito de
    # django-cors-headers) para poder agregar los headers CORS a toda
    # respuesta, incluidas las de error.
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Publica el request actual para que los signals de auditoría (HU13)
    # sepan qué usuario hizo cada cambio.
    "apps.auditoria.interfaces.middleware.RequestActualMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# DATABASE_URL vive en .env (ver .env.example) y apunta al servicio
# "postgres" de docker-compose.yml en desarrollo.
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Cada app guarda sus migraciones en infrastructure/migrations/ en vez de
# en "<app>/migrations/" (la ubicación default de Django), para que TODO lo
# relacionado al ORM (modelos + migraciones) quede junto dentro de la capa
# infrastructure, consistente con Clean Architecture. indicadores no
# aparece acá porque no tiene modelos propios.
MIGRATION_MODULES = {
    "usuarios": "apps.usuarios.infrastructure.migrations",
    "catalogo": "apps.catalogo.infrastructure.migrations",
    "movimientos": "apps.movimientos.infrastructure.migrations",
    "transferencias": "apps.transferencias.infrastructure.migrations",
    "auditoria": "apps.auditoria.infrastructure.migrations",
}

AUTH_USER_MODEL = "usuarios.Usuario"


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "es"
TIME_ZONE = "UTC"  # ajustar a la zona horaria real del negocio si aplica
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# SimpleJWT (autenticación JWT con los 3 roles: el rol vive en el modelo
# Usuario, no en la config de JWT; ver
# apps/usuarios/interfaces/api/serializers.py::CustomTokenObtainPairSerializer
# para cómo se agrega como claim del token).
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# drf-spectacular (Swagger / OpenAPI)
SPECTACULAR_SETTINGS = {
    "TITLE": "Inventario Multisucursal API",
    "DESCRIPTION": "API de inventario para importadora de herramientas (2 sucursales).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# CORS: el frontend (Vite, puerto 5173) corre en un origen distinto al
# backend (puerto 8000). Sin esto el navegador bloquea las peticiones de
# Axios/TanStack Query aunque el backend responda bien.
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"]
)
