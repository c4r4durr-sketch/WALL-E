from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ...domain.value_objects import Rol
from ...infrastructure.models import Sucursal


class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ["id", "nombre", "direccion", "activa"]
        read_only_fields = ["id"]


class UsuarioSerializer(serializers.Serializer):
    """
    Serializer "plano": solo valida la FORMA de los datos y serializa la
    entidad de dominio. Las reglas (username único, sucursal obligatoria,
    política de contraseñas, proteger al último Administrador) las aplica
    use_cases/gestionar_usuarios.py. Los nombres de la API (first_name,
    is_active, sucursal) se conservan; `source` los traduce a los del
    dominio (nombres, activo, sucursal_id).
    """

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150)
    # write_only: nunca se devuelve. Opcional en la forma; el use case la
    # exige al crear. Editar sin enviarla conserva la actual (HU3, CA3).
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=False, trim_whitespace=False,
        style={"input_type": "password"},
    )
    first_name = serializers.CharField(source="nombres", max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(source="apellidos", max_length=150, required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    rol = serializers.ChoiceField(choices=[r.value for r in Rol], required=False, default=Rol.EMPLEADO.value)
    sucursal = serializers.IntegerField(source="sucursal_id", required=False, allow_null=True, default=None)
    sucursal_nombre = serializers.CharField(read_only=True, allow_null=True)
    is_active = serializers.BooleanField(source="activo", required=False, default=True)


class RestablecerPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extiende el serializer de SimpleJWT para incluir `rol` y `sucursal`
    como claims del access token. El frontend los necesita apenas hace
    login (para mostrar/ocultar UI por rol) sin tener que pegarle a un
    segundo endpoint "/me/".

    Esto es configuración de autenticación, no lógica de negocio: no decide
    nada, solo copia datos ya existentes del usuario al token.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["rol"] = user.rol
        token["sucursal_id"] = user.sucursal_id
        token["sucursal_nombre"] = user.sucursal.nombre if user.sucursal_id else None
        return token
