"""
Serializers para la API móvil
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from apps.bienes.models import BienPatrimonial, HistorialEstado
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina


class UserSerializer(serializers.ModelSerializer):
    """Serializer para información básica del usuario"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'username', 'is_staff', 'is_superuser']


class CatalogoSerializer(serializers.ModelSerializer):
    """Serializer para el catálogo de bienes"""
    
    class Meta:
        model = Catalogo
        fields = ['id', 'codigo', 'denominacion', 'grupo', 'clase', 'resolucion', 'estado']


class OficinaSerializer(serializers.ModelSerializer):
    """Serializer para oficinas"""
    
    class Meta:
        model = Oficina
        fields = ['id', 'codigo', 'nombre', 'descripcion', 'responsable', 'estado']


class BienPatrimonialListSerializer(serializers.ModelSerializer):
    """Serializer para lista de bienes patrimoniales (vista resumida)"""
    catalogo_denominacion = serializers.CharField(source='catalogo.denominacion', read_only=True)
    oficina_nombre = serializers.CharField(source='oficina.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_bien_display', read_only=True)
    
    class Meta:
        model = BienPatrimonial
        fields = [
            'id', 'codigo_patrimonial', 'codigo_interno', 'catalogo_denominacion',
            'oficina_nombre', 'estado_bien', 'estado_display', 'marca', 'modelo',
            'color', 'serie', 'placa', 'matricula', 'qr_code', 'url_qr',
            'created_at', 'updated_at'
        ]


class BienPatrimonialDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para bienes patrimoniales"""
    catalogo = CatalogoSerializer(read_only=True)
    oficina = OficinaSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_bien_display', read_only=True)
    
    # IDs para escritura
    catalogo_id = serializers.IntegerField(write_only=True)
    oficina_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = BienPatrimonial
        fields = [
            'id', 'codigo_patrimonial', 'codigo_interno', 'catalogo', 'catalogo_id',
            'oficina', 'oficina_id', 'estado_bien', 'estado_display', 'marca', 'modelo',
            'color', 'serie', 'dimension', 'placa', 'matricula', 'nro_motor',
            'nro_chasis', 'observaciones', 'qr_code', 'url_qr', 'created_at',
            'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'qr_code', 'url_qr', 'created_at', 'updated_at', 'created_by']

    def validate_codigo_patrimonial(self, value):
        """Validar que el código patrimonial sea único"""
        if self.instance:
            # Si estamos actualizando, excluir el registro actual
            if BienPatrimonial.objects.exclude(pk=self.instance.pk).filter(codigo_patrimonial=value).exists():
                raise serializers.ValidationError("Ya existe un bien con este código patrimonial.")
        else:
            # Si estamos creando, verificar que no exista
            if BienPatrimonial.objects.filter(codigo_patrimonial=value).exists():
                raise serializers.ValidationError("Ya existe un bien con este código patrimonial.")
        return value

    def validate_catalogo_id(self, value):
        """Validar que el catálogo exista y esté activo"""
        try:
            catalogo = Catalogo.objects.get(pk=value)
            if catalogo.estado != 'ACTIVO':
                raise serializers.ValidationError("El catálogo seleccionado no está activo.")
        except Catalogo.DoesNotExist:
            raise serializers.ValidationError("El catálogo seleccionado no existe.")
        return value

    def validate_oficina_id(self, value):
        """Validar que la oficina exista y esté activa"""
        try:
            oficina = Oficina.objects.get(pk=value)
            if not oficina.estado:
                raise serializers.ValidationError("La oficina seleccionada no está activa.")
        except Oficina.DoesNotExist:
            raise serializers.ValidationError("La oficina seleccionada no existe.")
        return value


class HistorialEstadoSerializer(serializers.ModelSerializer):
    """Serializer para el historial de estados"""
    usuario = UserSerializer(read_only=True)
    estado_anterior_display = serializers.SerializerMethodField()
    estado_nuevo_display = serializers.SerializerMethodField()
    
    class Meta:
        model = HistorialEstado
        fields = [
            'id', 'bien', 'estado_anterior', 'estado_anterior_display',
            'estado_nuevo', 'estado_nuevo_display', 'observaciones',
            'fecha_cambio', 'usuario', 'ubicacion_gps', 'foto'
        ]
        read_only_fields = ['id', 'fecha_cambio', 'usuario']

    def get_estado_anterior_display(self, obj):
        """Obtener el display del estado anterior"""
        return dict(BienPatrimonial.ESTADOS_BIEN).get(obj.estado_anterior, obj.estado_anterior)

    def get_estado_nuevo_display(self, obj):
        """Obtener el display del estado nuevo"""
        return dict(BienPatrimonial.ESTADOS_BIEN).get(obj.estado_nuevo, obj.estado_nuevo)


class ActualizarEstadoSerializer(serializers.Serializer):
    """Serializer para actualizar el estado de un bien desde móvil"""
    estado_bien = serializers.ChoiceField(choices=BienPatrimonial.ESTADOS_BIEN)
    observaciones = serializers.CharField(required=False, allow_blank=True)
    ubicacion_gps = serializers.CharField(required=False, allow_blank=True)
    foto = serializers.ImageField(required=False)

    def validate_estado_bien(self, value):
        """Validar que el estado requiera observaciones si es necesario"""
        if value in ['M', 'E', 'C']:  # MALO, RAEE, CHATARRA
            observaciones = self.initial_data.get('observaciones', '')
            if not observaciones or not observaciones.strip():
                raise serializers.ValidationError(
                    "Las observaciones son obligatorias para estados MALO, RAEE o CHATARRA."
                )
        return value


# Serializers para sincronización offline
from .models import CambioOffline, SesionSync, ConflictoSync


class CambioOfflineSerializer(serializers.ModelSerializer):
    """Serializer para cambios offline"""
    
    class Meta:
        model = CambioOffline
        fields = [
            'id', 'tipo_cambio', 'timestamp_local', 'bien_codigo_patrimonial',
            'bien_qr_code', 'datos_cambio', 'estado_sync', 'dispositivo_id',
            'ubicacion_gps', 'mensaje_error', 'created_at'
        ]
        read_only_fields = ['id', 'estado_sync', 'mensaje_error', 'created_at']

    def validate_timestamp_local(self, value):
        """Validar que el timestamp local sea válido"""
        from datetime import datetime, timedelta
        
        # Verificar que no sea muy antiguo (más de 30 días)
        limite = datetime.now() - timedelta(days=30)
        if value < limite.replace(tzinfo=value.tzinfo):
            raise serializers.ValidationError("El timestamp es muy antiguo")
        
        return value


class SincronizarCambiosSerializer(serializers.Serializer):
    """Serializer para sincronizar múltiples cambios"""
    dispositivo_id = serializers.CharField(max_length=100)
    cambios = CambioOfflineSerializer(many=True)
    
    def validate_cambios(self, value):
        """Validar que haya cambios para sincronizar"""
        if not value:
            raise serializers.ValidationError("Se requiere al menos un cambio para sincronizar")
        return value


class ConflictoSyncSerializer(serializers.ModelSerializer):
    """Serializer para conflictos de sincronización"""
    cambio_offline = CambioOfflineSerializer(read_only=True)
    
    class Meta:
        model = ConflictoSync
        fields = [
            'id', 'cambio_offline', 'tipo_conflicto', 'datos_servidor',
            'datos_cliente', 'resuelto', 'resolucion_elegida', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ResolverConflictoSerializer(serializers.Serializer):
    """Serializer para resolver conflictos"""
    conflicto_id = serializers.IntegerField()
    resolucion = serializers.ChoiceField(choices=[
        ('SERVIDOR', 'Mantener datos del servidor'),
        ('CLIENTE', 'Aplicar datos del cliente'),
        ('MANUAL', 'Resolución manual'),
    ])
    datos_manuales = serializers.JSONField(required=False)
    
    def validate(self, attrs):
        """Validar que si es resolución manual, se proporcionen los datos"""
        if attrs['resolucion'] == 'MANUAL' and not attrs.get('datos_manuales'):
            raise serializers.ValidationError(
                "Se requieren datos manuales para resolución manual"
            )
        return attrs


class SesionSyncSerializer(serializers.ModelSerializer):
    """Serializer para sesiones de sincronización"""
    
    class Meta:
        model = SesionSync
        fields = [
            'id', 'dispositivo_id', 'inicio_sync', 'fin_sync', 'cambios_pendientes',
            'cambios_procesados', 'cambios_exitosos', 'cambios_con_error',
            'cambios_con_conflicto', 'completada', 'mensaje_resultado'
        ]
        read_only_fields = ['id', 'inicio_sync', 'fin_sync']