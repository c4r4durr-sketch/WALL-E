"""
Value objects del dominio de usuarios.

Un Enum de Python puro (sin heredar de ningún tipo de Django) para que
use_cases pueda comparar/validar roles sin importar Django. El modelo ORM
(infrastructure/models.py) usa estos mismos valores como choices, así que
solo existe UNA fuente de verdad para los roles válidos.
"""

from enum import Enum


class Rol(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    SUPERVISOR = "SUPERVISOR"
    EMPLEADO = "EMPLEADO"
