from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ...infrastructure.models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "rol",
            "sucursal",
            "is_active",
        ]
        read_only_fields = ["id"]


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
        token["rol"] = user.rol
        token["sucursal_id"] = user.sucursal_id
        return token
