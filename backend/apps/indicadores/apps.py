from django.apps import AppConfig


class IndicadoresConfig(AppConfig):
    """
    App de indicadores: EOQ, Punto de Reorden (ROP) y clasificación ABC.

    A propósito NO tiene modelos propios (no hay infrastructure/models.py):
    todo lo que necesita ya existe como movimientos históricos (apps
    movimientos) y datos de producto (apps catalogo). Sus use_cases son
    funciones puras que combinan esos datos; no persiste nada nuevo.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.indicadores"
    label = "indicadores"
