"""
Reglas de formato compartidas por los formularios de todos los módulos
(nombres de personas, usuario, teléfono, código de herramienta, política
de contraseñas). Puras: sin Django, las usan los casos de uso.

Cada función devuelve el mensaje de error (en español) o None si el valor
es válido. Son las mismas reglas que aplica el frontend en
frontend/src/shared/validacion/: si cambia una, cambia la otra.

No es una app de Django (no tiene modelos ni está en INSTALLED_APPS): es
solo código compartido entre los 7 módulos.
"""

import re
from typing import Optional

# Nombres y apellidos de personas: letras (con tildes, ñ, ü), separadas
# por un espacio, un apóstrofo o un guion: "María José", "O'Brien",
# "Pérez-Gómez". [^\W\d_] es "una letra" en el re de Python.
NOMBRE_LARGO_MINIMO = 2
NOMBRE_LARGO_MAXIMO = 50
_NOMBRE_VALIDO = re.compile(r"[^\W\d_]+(?:[ '’-][^\W\d_]+)*")

# Usuario: letras sin tildes, números, punto, guion y guion bajo.
USERNAME_LARGO_MINIMO = 3
USERNAME_LARGO_MAXIMO = 30
_USERNAME_VALIDO = re.compile(r"[A-Za-z0-9._-]+")

# Teléfono: dígitos con espacios o guiones opcionales y un "+" inicial
# para el código de país: "+591 2 2123456", "777-12345".
TELEFONO_MIN_DIGITOS = 7
TELEFONO_MAX_DIGITOS = 15
_TELEFONO_VALIDO = re.compile(r"\+?[\d -]+")

# Código de herramienta: mayúsculas, números y guiones entre ellos.
CODIGO_LARGO_MAXIMO = 30
_CODIGO_VALIDO = re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)*")

# Textos libres (motivos, observaciones).
TEXTO_LARGO_MAXIMO = 255

PASSWORD_LARGO_MINIMO = 8


def normalizar_espacios(valor: Optional[str]) -> str:
    """Quita los espacios del inicio y del final y deja uno solo entre
    palabras. Un texto de puros espacios queda vacío."""
    return " ".join((valor or "").split())


def error_nombre_persona(valor: str, etiqueta: str = "El nombre") -> Optional[str]:
    """`valor` ya normalizado con normalizar_espacios."""
    if not valor:
        return f"{etiqueta} es obligatorio."
    if not NOMBRE_LARGO_MINIMO <= len(valor) <= NOMBRE_LARGO_MAXIMO:
        return f"Debe tener de {NOMBRE_LARGO_MINIMO} a {NOMBRE_LARGO_MAXIMO} caracteres."
    if not _NOMBRE_VALIDO.fullmatch(valor):
        return "Solo letras, espacios, apóstrofo y guion (sin números ni símbolos)."
    return None


def error_username(valor: str) -> Optional[str]:
    if not valor:
        return "El usuario es obligatorio."
    if not USERNAME_LARGO_MINIMO <= len(valor) <= USERNAME_LARGO_MAXIMO:
        return f"Debe tener de {USERNAME_LARGO_MINIMO} a {USERNAME_LARGO_MAXIMO} caracteres."
    if not _USERNAME_VALIDO.fullmatch(valor):
        return "Solo letras sin tildes, números, punto, guion y guion bajo (sin espacios)."
    return None


def error_telefono(valor: str) -> Optional[str]:
    if not valor:
        return "El teléfono es obligatorio."
    digitos = sum(c.isdigit() for c in valor)
    if not _TELEFONO_VALIDO.fullmatch(valor) or not TELEFONO_MIN_DIGITOS <= digitos <= TELEFONO_MAX_DIGITOS:
        return (
            f"De {TELEFONO_MIN_DIGITOS} a {TELEFONO_MAX_DIGITOS} dígitos; "
            "solo números, espacios, guiones y + al inicio."
        )
    return None


def normalizar_codigo(valor: Optional[str]) -> str:
    return (valor or "").strip().upper()


def error_codigo(valor: str) -> Optional[str]:
    """`valor` ya normalizado con normalizar_codigo."""
    if not valor:
        return "El código es obligatorio."
    if len(valor) > CODIGO_LARGO_MAXIMO:
        return f"No puede tener más de {CODIGO_LARGO_MAXIMO} caracteres."
    if not _CODIGO_VALIDO.fullmatch(valor):
        return "Solo letras, números y guiones entre ellos (sin espacios)."
    return None


def error_texto(valor: str, etiqueta: str, *, obligatorio: bool, maximo: int = TEXTO_LARGO_MAXIMO) -> Optional[str]:
    """Textos libres: `valor` ya sin espacios sobrantes."""
    if obligatorio and not valor:
        return f"{etiqueta} es obligatorio."
    if len(valor) > maximo:
        return f"No puede tener más de {maximo} caracteres."
    return None


def faltantes_password(password: str) -> list[str]:
    """Lo que le falta a la contraseña de la política propia (mayúscula,
    minúscula, número y símbolo). El largo mínimo, las comunes y la
    parecida al usuario las revisan los validadores de Django."""
    faltan = []
    if not any(c.isupper() for c in password):
        faltan.append("una mayúscula")
    if not any(c.islower() for c in password):
        faltan.append("una minúscula")
    if not any(c.isdigit() for c in password):
        faltan.append("un número")
    if not any(not c.isalnum() and not c.isspace() for c in password):
        faltan.append("un símbolo")
    return faltan
