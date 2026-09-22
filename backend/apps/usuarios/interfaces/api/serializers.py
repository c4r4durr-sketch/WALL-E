from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ...domain.reglas import requiere_sucursal
from ...infrastructure.models import Sucursal, Usuario


class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ["id", "nombre", "direccion", "activa"]
        read_only_fields = ["id"]


class UsuarioSerializer(serializers.ModelSerializer):
    # write_only: nunca se devuelve en la respuesta. Se hashea en create()
    # (nunca se guarda en texto plano); required solo al crear, no al
    # editar (un PATCH sin password no debe borrarla).
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "rol",
            "sucursal",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        # En un PATCH parcial pueden venir solo el rol o solo la sucursal:
        # se combina con lo que ya tiene el usuario para validar el estado
        # final, no solo los campos enviados.
        rol = attrs.get("rol", getattr(self.instance, "rol", None))
        if "sucursal" in attrs:
            sucursal = attrs["sucursal"]
        else:
            sucursal = getattr(self.instance, "sucursal", None)

        if rol is not None and requiere_sucursal(rol) and sucursal is None:
            raise serializers.ValidationError(
                {"sucursal": "Supervisor y Empleado deben tener una sucursal asignada."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        usuario = Usuario(**validated_data)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        usuario = super().update(instance, validated_data)
        if password:
            usuario.set_password(password)
            usuario.save()
        return usuario


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
