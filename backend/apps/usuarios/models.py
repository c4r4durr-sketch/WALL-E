# Puente hacia infrastructure/models.py.
#
# Django exige que los modelos de una app vivan en "<app>/models.py" (o en un
# paquete "<app>/models/") para poder registrarlos en el app registry. Como
# en Clean Architecture los modelos ORM son un detalle de infraestructura,
# los definimos en infrastructure/models.py y este archivo solo los
# reexporta, para no pelear contra las convenciones de Django.
from .infrastructure.models import *  # noqa: F401,F403
