"""
Validador propio de contraseñas, registrado en AUTH_PASSWORD_VALIDATORS
junto a los de Django. Exige lo que los de Django no piden: una
mayúscula, una minúscula, un número y un símbolo. Así el backend pide lo
mismo que la barra de seguridad del frontend (PasswordStrength). La regla
vive en apps/comun/reglas.py; esto solo la conecta con Django.
"""

from django.core.exceptions import ValidationError

from apps.comun.reglas import faltantes_password


class ComplejidadPasswordValidator:
    def validate(self, password, user=None):
        faltan = faltantes_password(password)
        if faltan:
            lista = ", ".join(faltan[:-1]) + (" y " if len(faltan) > 1 else "") + faltan[-1]
            raise ValidationError(f"La contraseña debe tener al menos {lista}.", code="password_sin_complejidad")

    def get_help_text(self):
        return "La contraseña debe tener al menos una mayúscula, una minúscula, un número y un símbolo."
