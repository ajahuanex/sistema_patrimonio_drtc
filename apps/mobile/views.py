"""
Views para la API móvil del sistema de patrimonio
"""
from rest_framework import status, viewsets, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from apps.bienes.models import BienPatrimonial, HistorialEstado
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from .serializers import (
    BienPatrimonialListSerializer, BienPatrimonialDetailSerializer,
    CatalogoSerializer, OficinaSerializer, HistorialEstadoSerializer,
    ActualizarEstadoSerializer
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para JWT que incluye información del usuario"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar información personalizada al token
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar información del usuario a la respuesta
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
        }
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener tokens JWT"""
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """Vista personalizada para refrescar tokens JWT"""
    pass


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint de login que retorna tokens JWT
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username y password son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user:
        if user.is_active:
            serializer = CustomTokenObtainPairSerializer()
            token = serializer.get_token(user)
            
            return Response({
                'access': str(token.access_token),
                'refresh': str(token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Usuario inactivo'
            }, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({
            'error': 'Credenciales inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_view(request):
    """
    Endpoint de logout (principalmente para limpiar el lado del cliente)
    """
    return Response({
        'message': 'Logout exitoso'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def user_profile_view(request):
    """
    Endpoint para obtener información del usuario autenticado
    """
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }, status=status.HTTP_200_OK)


class BienPatrimonialViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de bienes patrimoniales
    """
    queryset = BienPatrimonial.objects.select_related('catalogo', 'oficina', 'created_by').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtros disponibles
    filterset_fields = {
        'estado_bien': ['exact', 'in'],
        'oficina': ['exact'],
        'catalogo': ['exact'],
        'marca': ['icontains'],
        'modelo': ['icontains'],
        'created_at': ['gte', 'lte', 'exact'],
        'updated_at': ['gte', 'lte', 'exact'],
    }
    
    # Campos de búsqueda
    search_fields = [
        'codigo_patrimonial', 'codigo_interno', 'catalogo__denominacion',
        'marca', 'modelo', 'serie', 'placa', 'matricula', 'nro_motor', 'nro_chasis'
    ]
    
    # Campos de ordenamiento
    ordering_fields = ['codigo_patrimonial', 'created_at', 'updated_at', 'estado_bien']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Usar serializer diferente para lista vs detalle"""
        if self.action == 'list':
            return BienPatrimonialListSerializer
        return BienPatrimonialDetailSerializer

    def perform_create(self, serializer):
        """Asignar el usuario actual como creador"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='buscar-por-qr/(?P<qr_code>[^/.]+)')
    def buscar_por_qr(self, request, qr_code=None):
        """
        Endpoint específico para buscar un bien por código QR
        """
        try:
            bien = BienPatrimonial.objects.select_related('catalogo', 'oficina', 'created_by').get(qr_code=qr_code)
            serializer = BienPatrimonialDetailSerializer(bien)
            return Response(serializer.data)
        except BienPatrimonial.DoesNotExist:
            return Response({
                'error': 'No se encontró un bien con este código QR'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """
        Obtener el historial de estados de un bien
        """
        bien = self.get_object()
        historial = HistorialEstado.objects.filter(bien=bien).select_related('usuario').order_by('-fecha_cambio')
        serializer = HistorialEstadoSerializer(historial, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas básicas de bienes
        """
        from django.db.models import Count
        
        # Contar por estado
        estados = BienPatrimonial.objects.values('estado_bien').annotate(
            count=Count('id')
        ).order_by('estado_bien')
        
        # Contar por oficina
        oficinas = BienPatrimonial.objects.values(
            'oficina__nombre'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # Top 10 oficinas
        
        # Total de bienes
        total = BienPatrimonial.objects.count()
        
        return Response({
            'total_bienes': total,
            'por_estado': list(estados),
            'top_oficinas': list(oficinas),
        })

    @action(detail=True, methods=['post'])
    def actualizar_estado(self, request, pk=None):
        """
        Actualizar el estado de un bien desde dispositivo móvil
        """
        bien = self.get_object()
        serializer = ActualizarEstadoSerializer(data=request.data)
        
        if serializer.is_valid():
            estado_anterior = bien.estado_bien
            nuevo_estado = serializer.validated_data['estado_bien']
            observaciones = serializer.validated_data.get('observaciones', '')
            ubicacion_gps = serializer.validated_data.get('ubicacion_gps', '')
            foto = serializer.validated_data.get('foto')
            
            # Actualizar el estado del bien
            bien.estado_bien = nuevo_estado
            bien.save()
            
            # Crear registro en el historial
            historial = HistorialEstado.objects.create(
                bien=bien,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                observaciones=observaciones,
                usuario=request.user,
                ubicacion_gps=ubicacion_gps,
                foto=foto
            )
            
            # Retornar información actualizada
            bien_serializer = BienPatrimonialDetailSerializer(bien)
            historial_serializer = HistorialEstadoSerializer(historial)
            
            return Response({
                'message': 'Estado actualizado correctamente',
                'bien': bien_serializer.data,
                'historial': historial_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def capturar_foto(self, request, pk=None):
        """
        Capturar y asociar una foto a un bien patrimonial
        """
        bien = self.get_object()
        foto = request.FILES.get('foto')
        observaciones = request.data.get('observaciones', '')
        ubicacion_gps = request.data.get('ubicacion_gps', '')
        
        if not foto:
            return Response({
                'error': 'Se requiere una foto'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear registro en el historial con la foto
        historial = HistorialEstado.objects.create(
            bien=bien,
            estado_anterior=bien.estado_bien,
            estado_nuevo=bien.estado_bien,  # Mismo estado
            observaciones=observaciones or 'Foto capturada desde dispositivo móvil',
            usuario=request.user,
            ubicacion_gps=ubicacion_gps,
            foto=foto
        )
        
        historial_serializer = HistorialEstadoSerializer(historial)
        
        return Response({
            'message': 'Foto capturada correctamente',
            'historial': historial_serializer.data
        }, status=status.HTTP_201_CREATED)


class CatalogoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para el catálogo
    """
    queryset = Catalogo.objects.filter(estado='ACTIVO').order_by('denominacion')
    serializer_class = CatalogoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['grupo', 'clase']
    search_fields = ['codigo', 'denominacion', 'grupo', 'clase']
    ordering_fields = ['codigo', 'denominacion', 'grupo', 'clase']
    ordering = ['denominacion']


class OficinaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para oficinas
    """
    queryset = Oficina.objects.filter(estado=True).order_by('nombre')
    serializer_class = OficinaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    
    search_fields = ['codigo', 'nombre', 'responsable']
    ordering_fields = ['codigo', 'nombre']
    ordering = ['nombre']


@api_view(['POST'])
def scan_qr_mobile(request):
    """
    Endpoint para procesar escaneo QR desde móvil
    """
    qr_code = request.data.get('qr_code')
    
    if not qr_code:
        return Response({
            'error': 'Código QR requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        bien = BienPatrimonial.objects.select_related('catalogo', 'oficina', 'created_by').get(qr_code=qr_code)
        
        # Información básica siempre disponible
        data = {
            'bien': BienPatrimonialDetailSerializer(bien).data,
            'puede_editar': False,
            'puede_actualizar_estado': False
        }
        
        # Si el usuario está autenticado, agregar permisos
        if request.user.is_authenticated:
            data['puede_editar'] = request.user.is_staff or request.user.is_superuser
            data['puede_actualizar_estado'] = True
        
        return Response(data, status=status.HTTP_200_OK)
        
    except BienPatrimonial.DoesNotExist:
        return Response({
            'error': 'No se encontró un bien con este código QR'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def inventario_rapido(request):
    """
    Endpoint para inventario rápido escaneando múltiples QR
    """
    codigos_qr = request.data.get('codigos_qr', [])
    ubicacion_gps = request.data.get('ubicacion_gps', '')
    observaciones = request.data.get('observaciones', 'Inventario rápido desde móvil')
    
    if not codigos_qr:
        return Response({
            'error': 'Se requiere al menos un código QR'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    resultados = []
    errores = []
    
    for qr_code in codigos_qr:
        try:
            bien = BienPatrimonial.objects.get(qr_code=qr_code)
            
            # Crear registro de inventario
            historial = HistorialEstado.objects.create(
                bien=bien,
                estado_anterior=bien.estado_bien,
                estado_nuevo=bien.estado_bien,
                observaciones=observaciones,
                usuario=request.user,
                ubicacion_gps=ubicacion_gps
            )
            
            resultados.append({
                'qr_code': qr_code,
                'codigo_patrimonial': bien.codigo_patrimonial,
                'denominacion': bien.catalogo.denominacion,
                'estado': 'inventariado'
            })
            
        except BienPatrimonial.DoesNotExist:
            errores.append({
                'qr_code': qr_code,
                'error': 'Bien no encontrado'
            })
    
    return Response({
        'inventariados': len(resultados),
        'errores': len(errores),
        'resultados': resultados,
        'errores_detalle': errores
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def dashboard_mobile(request):
    """
    Dashboard con información resumida para móvil
    """
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    # Estadísticas generales
    total_bienes = BienPatrimonial.objects.count()
    
    # Bienes por estado
    estados = BienPatrimonial.objects.values('estado_bien').annotate(
        count=Count('id')
    ).order_by('estado_bien')
    
    # Actividad reciente (últimos 7 días)
    fecha_limite = datetime.now() - timedelta(days=7)
    actividad_reciente = HistorialEstado.objects.filter(
        fecha_cambio__gte=fecha_limite
    ).count()
    
    # Bienes que requieren atención (MALO, RAEE, CHATARRA)
    requieren_atencion = BienPatrimonial.objects.filter(
        estado_bien__in=['M', 'E', 'C']
    ).count()
    
    return Response({
        'total_bienes': total_bienes,
        'estados': list(estados),
        'actividad_reciente': actividad_reciente,
        'requieren_atencion': requieren_atencion,
        'usuario': {
            'username': request.user.username,
            'nombre_completo': f"{request.user.first_name} {request.user.last_name}".strip(),
            'es_admin': request.user.is_staff or request.user.is_superuser
        }
    }, status=status.HTTP_200_OK)


# Vistas para sincronización offline
from .models import CambioOffline, SesionSync, ConflictoSync
from .serializers import (
    CambioOfflineSerializer, SincronizarCambiosSerializer,
    ConflictoSyncSerializer, ResolverConflictoSerializer, SesionSyncSerializer
)
from .tasks import procesar_sincronizacion_async


@api_view(['POST'])
def sincronizar_cambios(request):
    """
    Endpoint para sincronizar cambios offline
    """
    serializer = SincronizarCambiosSerializer(data=request.data)
    
    if serializer.is_valid():
        dispositivo_id = serializer.validated_data['dispositivo_id']
        cambios_data = serializer.validated_data['cambios']
        
        # Crear sesión de sincronización
        sesion = SesionSync.objects.create(
            usuario=request.user,
            dispositivo_id=dispositivo_id,
            cambios_pendientes=len(cambios_data)
        )
        
        # Crear registros de cambios offline
        cambios_creados = []
        for cambio_data in cambios_data:
            cambio = CambioOffline.objects.create(
                usuario=request.user,
                **cambio_data
            )
            cambios_creados.append(cambio)
        
        # Procesar sincronización de forma asíncrona
        procesar_sincronizacion_async.delay(sesion.id, [c.id for c in cambios_creados])
        
        return Response({
            'sesion_id': sesion.id,
            'cambios_recibidos': len(cambios_creados),
            'mensaje': 'Sincronización iniciada. Use el endpoint de estado para verificar el progreso.'
        }, status=status.HTTP_202_ACCEPTED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def estado_sincronizacion(request, sesion_id):
    """
    Obtener el estado de una sesión de sincronización
    """
    try:
        sesion = SesionSync.objects.get(id=sesion_id, usuario=request.user)
        serializer = SesionSyncSerializer(sesion)
        
        # Obtener conflictos pendientes si los hay
        conflictos = ConflictoSync.objects.filter(
            cambio_offline__usuario=request.user,
            resuelto=False
        ).select_related('cambio_offline')
        
        conflictos_data = ConflictoSyncSerializer(conflictos, many=True).data
        
        return Response({
            'sesion': serializer.data,
            'conflictos_pendientes': conflictos_data
        }, status=status.HTTP_200_OK)
        
    except SesionSync.DoesNotExist:
        return Response({
            'error': 'Sesión de sincronización no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def resolver_conflicto(request):
    """
    Resolver un conflicto de sincronización
    """
    serializer = ResolverConflictoSerializer(data=request.data)
    
    if serializer.is_valid():
        conflicto_id = serializer.validated_data['conflicto_id']
        resolucion = serializer.validated_data['resolucion']
        datos_manuales = serializer.validated_data.get('datos_manuales')
        
        try:
            conflicto = ConflictoSync.objects.get(
                id=conflicto_id,
                cambio_offline__usuario=request.user,
                resuelto=False
            )
            
            # Marcar conflicto como resuelto
            conflicto.resuelto = True
            conflicto.resolucion_elegida = resolucion
            conflicto.save()
            
            # Actualizar el cambio offline
            cambio = conflicto.cambio_offline
            cambio.conflicto_resuelto = True
            cambio.resuelto_por = request.user
            cambio.fecha_resolucion = timezone.now()
            
            # Aplicar la resolución
            if resolucion == 'CLIENTE':
                # Aplicar los datos del cliente
                cambio.estado_sync = 'PENDIENTE'
                cambio.save()
                # Reintentará procesarse automáticamente
                
            elif resolucion == 'MANUAL':
                # Aplicar los datos manuales
                cambio.datos_cambio = datos_manuales
                cambio.estado_sync = 'PENDIENTE'
                cambio.save()
                
            else:  # SERVIDOR
                # Descartar el cambio del cliente
                cambio.estado_sync = 'COMPLETADO'
                cambio.save()
            
            return Response({
                'mensaje': 'Conflicto resuelto correctamente'
            }, status=status.HTTP_200_OK)
            
        except ConflictoSync.DoesNotExist:
            return Response({
                'error': 'Conflicto no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def cambios_pendientes(request):
    """
    Obtener cambios pendientes de sincronización para el usuario
    """
    cambios = CambioOffline.objects.filter(
        usuario=request.user,
        estado_sync__in=['PENDIENTE', 'ERROR']
    ).order_by('-timestamp_local')
    
    serializer = CambioOfflineSerializer(cambios, many=True)
    
    return Response({
        'cambios_pendientes': len(cambios),
        'cambios': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def reintentar_sincronizacion(request):
    """
    Reintentar sincronización de cambios con error
    """
    dispositivo_id = request.data.get('dispositivo_id')
    
    if not dispositivo_id:
        return Response({
            'error': 'dispositivo_id requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Obtener cambios con error
    cambios_error = CambioOffline.objects.filter(
        usuario=request.user,
        dispositivo_id=dispositivo_id,
        estado_sync='ERROR'
    )
    
    if not cambios_error.exists():
        return Response({
            'mensaje': 'No hay cambios con error para reintentar'
        }, status=status.HTTP_200_OK)
    
    # Crear nueva sesión de sincronización
    sesion = SesionSync.objects.create(
        usuario=request.user,
        dispositivo_id=dispositivo_id,
        cambios_pendientes=cambios_error.count()
    )
    
    # Marcar cambios como pendientes
    cambios_error.update(estado_sync='PENDIENTE', intentos_sync=0)
    
    # Procesar de forma asíncrona
    procesar_sincronizacion_async.delay(sesion.id, list(cambios_error.values_list('id', flat=True)))
    
    return Response({
        'sesion_id': sesion.id,
        'cambios_reintentados': cambios_error.count(),
        'mensaje': 'Reintento de sincronización iniciado'
    }, status=status.HTTP_202_ACCEPTED)