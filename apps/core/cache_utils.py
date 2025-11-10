"""
Utilidades de caché para el sistema de papelera de reciclaje.
Implementa estrategias de caché para mejorar el rendimiento de consultas frecuentes.
"""
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import hashlib
import json


class RecycleBinCache:
    """
    Clase para gestionar el caché de estadísticas de la papelera de reciclaje.
    Implementa estrategias de invalidación y actualización de caché.
    """
    
    # Prefijos de claves de caché
    PREFIX_STATS = 'recycle_stats'
    PREFIX_MODULE_STATS = 'recycle_module_stats'
    PREFIX_USER_STATS = 'recycle_user_stats'
    PREFIX_DASHBOARD = 'recycle_dashboard'
    PREFIX_COUNT = 'recycle_count'
    
    # Tiempos de expiración (en segundos)
    TIMEOUT_SHORT = 300  # 5 minutos
    TIMEOUT_MEDIUM = 900  # 15 minutos
    TIMEOUT_LONG = 1800  # 30 minutos
    
    @classmethod
    def _generate_cache_key(cls, prefix, *args, **kwargs):
        """
        Genera una clave de caché única basada en los parámetros.
        
        Args:
            prefix: Prefijo de la clave
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
            
        Returns:
            str: Clave de caché única
        """
        # Crear string con todos los parámetros
        params_str = f"{prefix}:{':'.join(map(str, args))}"
        
        # Agregar kwargs ordenados
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = ':'.join(f"{k}={v}" for k, v in sorted_kwargs)
            params_str += f":{kwargs_str}"
        
        # Generar hash para claves largas
        if len(params_str) > 200:
            params_hash = hashlib.md5(params_str.encode()).hexdigest()
            return f"{prefix}:{params_hash}"
        
        return params_str
    
    @classmethod
    def get_general_stats(cls, user_id=None, days=30):
        """
        Obtiene estadísticas generales de la papelera con caché.
        
        Args:
            user_id: ID del usuario (None para todos)
            days: Días a considerar
            
        Returns:
            dict: Estadísticas generales
        """
        cache_key = cls._generate_cache_key(
            cls.PREFIX_STATS,
            user_id=user_id,
            days=days
        )
        
        # Intentar obtener del caché
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Calcular estadísticas
        from apps.core.models import RecycleBin
        
        queryset = RecycleBin.objects.all()
        
        if user_id:
            queryset = queryset.filter(deleted_by_id=user_id)
        
        if days > 0:
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(deleted_at__gte=start_date)
        
        stats = {
            'total_deleted': queryset.count(),
            'total_restored': queryset.filter(restored_at__isnull=False).count(),
            'total_pending': queryset.filter(restored_at__isnull=True).count(),
            'near_auto_delete': queryset.filter(
                restored_at__isnull=True,
                auto_delete_at__lte=timezone.now() + timedelta(days=7),
                auto_delete_at__gt=timezone.now()
            ).count(),
            'ready_for_auto_delete': queryset.filter(
                restored_at__isnull=True,
                auto_delete_at__lte=timezone.now()
            ).count(),
        }
        
        # Guardar en caché
        cache.set(cache_key, stats, cls.TIMEOUT_MEDIUM)
        
        return stats
    
    @classmethod
    def get_module_stats(cls, user_id=None, days=30):
        """
        Obtiene estadísticas por módulo con caché.
        
        Args:
            user_id: ID del usuario (None para todos)
            days: Días a considerar
            
        Returns:
            list: Estadísticas por módulo
        """
        cache_key = cls._generate_cache_key(
            cls.PREFIX_MODULE_STATS,
            user_id=user_id,
            days=days
        )
        
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        from apps.core.models import RecycleBin
        
        queryset = RecycleBin.objects.all()
        
        if user_id:
            queryset = queryset.filter(deleted_by_id=user_id)
        
        if days > 0:
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(deleted_at__gte=start_date)
        
        stats = list(queryset.values('module_name').annotate(
            total=Count('id'),
            restored=Count('id', filter=Q(restored_at__isnull=False)),
            pending=Count('id', filter=Q(restored_at__isnull=True))
        ).order_by('-total'))
        
        cache.set(cache_key, stats, cls.TIMEOUT_MEDIUM)
        
        return stats
    
    @classmethod
    def get_user_stats(cls, days=30, limit=10):
        """
        Obtiene estadísticas por usuario con caché (solo para administradores).
        
        Args:
            days: Días a considerar
            limit: Número máximo de usuarios a retornar
            
        Returns:
            list: Estadísticas por usuario
        """
        cache_key = cls._generate_cache_key(
            cls.PREFIX_USER_STATS,
            days=days,
            limit=limit
        )
        
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        from apps.core.models import RecycleBin
        
        queryset = RecycleBin.objects.all()
        
        if days > 0:
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(deleted_at__gte=start_date)
        
        stats = list(queryset.values(
            'deleted_by_id',
            'deleted_by__username',
            'deleted_by__first_name',
            'deleted_by__last_name'
        ).annotate(
            total=Count('id'),
            restored=Count('id', filter=Q(restored_at__isnull=False)),
            pending=Count('id', filter=Q(restored_at__isnull=True))
        ).order_by('-total')[:limit])
        
        cache.set(cache_key, stats, cls.TIMEOUT_MEDIUM)
        
        return stats
    
    @classmethod
    def get_dashboard_data(cls, user_id, is_admin, days=30):
        """
        Obtiene todos los datos del dashboard con caché.
        
        Args:
            user_id: ID del usuario
            is_admin: Si el usuario es administrador
            days: Días a considerar
            
        Returns:
            dict: Datos completos del dashboard
        """
        cache_key = cls._generate_cache_key(
            cls.PREFIX_DASHBOARD,
            user_id=user_id,
            is_admin=is_admin,
            days=days
        )
        
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Construir datos del dashboard
        data = {
            'general_stats': cls.get_general_stats(
                user_id=None if is_admin else user_id,
                days=days
            ),
            'module_stats': cls.get_module_stats(
                user_id=None if is_admin else user_id,
                days=days
            ),
        }
        
        if is_admin:
            data['user_stats'] = cls.get_user_stats(days=days)
        
        cache.set(cache_key, data, cls.TIMEOUT_SHORT)
        
        return data
    
    @classmethod
    def get_count(cls, filters_hash):
        """
        Obtiene el conteo de elementos con caché para paginación eficiente.
        
        Args:
            filters_hash: Hash de los filtros aplicados
            
        Returns:
            int: Número de elementos
        """
        cache_key = cls._generate_cache_key(cls.PREFIX_COUNT, filters_hash)
        
        cached_count = cache.get(cache_key)
        if cached_count is not None:
            return cached_count
        
        # El conteo real se debe calcular fuera y pasar a set_count
        return None
    
    @classmethod
    def set_count(cls, filters_hash, count):
        """
        Guarda el conteo en caché.
        
        Args:
            filters_hash: Hash de los filtros aplicados
            count: Número de elementos
        """
        cache_key = cls._generate_cache_key(cls.PREFIX_COUNT, filters_hash)
        cache.set(cache_key, count, cls.TIMEOUT_SHORT)
    
    @classmethod
    def invalidate_all(cls):
        """
        Invalida todo el caché de la papelera de reciclaje.
        Debe llamarse cuando se realizan operaciones que afectan las estadísticas.
        """
        # Django no tiene una forma nativa de eliminar por patrón
        # Usamos un enfoque de versión de caché
        cache.delete_pattern(f"{cls.PREFIX_STATS}:*")
        cache.delete_pattern(f"{cls.PREFIX_MODULE_STATS}:*")
        cache.delete_pattern(f"{cls.PREFIX_USER_STATS}:*")
        cache.delete_pattern(f"{cls.PREFIX_DASHBOARD}:*")
        cache.delete_pattern(f"{cls.PREFIX_COUNT}:*")
    
    @classmethod
    def invalidate_user(cls, user_id):
        """
        Invalida el caché relacionado con un usuario específico.
        
        Args:
            user_id: ID del usuario
        """
        # Invalidar estadísticas del usuario
        cache.delete_pattern(f"{cls.PREFIX_STATS}:*user_id={user_id}*")
        cache.delete_pattern(f"{cls.PREFIX_DASHBOARD}:*user_id={user_id}*")
        
        # Invalidar estadísticas generales que incluyen este usuario
        cache.delete_pattern(f"{cls.PREFIX_USER_STATS}:*")
    
    @classmethod
    def invalidate_module(cls, module_name):
        """
        Invalida el caché relacionado con un módulo específico.
        
        Args:
            module_name: Nombre del módulo
        """
        cache.delete_pattern(f"{cls.PREFIX_MODULE_STATS}:*")
        cache.delete_pattern(f"{cls.PREFIX_STATS}:*")
        cache.delete_pattern(f"{cls.PREFIX_DASHBOARD}:*")


class QueryOptimizer:
    """
    Clase para optimizar consultas de la papelera de reciclaje.
    Implementa select_related y prefetch_related estratégicamente.
    """
    
    @staticmethod
    def optimize_recycle_bin_queryset(queryset):
        """
        Optimiza un queryset de RecycleBin con select_related y prefetch_related.
        
        Args:
            queryset: QuerySet de RecycleBin
            
        Returns:
            QuerySet optimizado
        """
        return queryset.select_related(
            'deleted_by',
            'deleted_by__profile',
            'restored_by',
            'restored_by__profile',
            'content_type'
        )
    
    @staticmethod
    def optimize_deletion_audit_queryset(queryset):
        """
        Optimiza un queryset de DeletionAuditLog.
        
        Args:
            queryset: QuerySet de DeletionAuditLog
            
        Returns:
            QuerySet optimizado
        """
        return queryset.select_related(
            'user',
            'user__profile',
            'content_type',
            'recycle_bin_entry'
        )
    
    @staticmethod
    def optimize_security_attempt_queryset(queryset):
        """
        Optimiza un queryset de SecurityCodeAttempt.
        
        Args:
            queryset: QuerySet de SecurityCodeAttempt
            
        Returns:
            QuerySet optimizado
        """
        return queryset.select_related(
            'user',
            'user__profile'
        )


class PaginationOptimizer:
    """
    Clase para optimizar la paginación en listados grandes.
    Implementa estrategias de paginación eficiente.
    """
    
    @staticmethod
    def get_optimized_page(queryset, page_number, page_size=20, use_cache=True):
        """
        Obtiene una página optimizada con caché de conteo.
        
        Args:
            queryset: QuerySet a paginar
            page_number: Número de página
            page_size: Tamaño de página
            use_cache: Si usar caché para el conteo
            
        Returns:
            tuple: (page_items, total_count, total_pages)
        """
        from django.core.paginator import Paginator
        
        # Generar hash de los filtros del queryset
        filters_hash = hashlib.md5(
            str(queryset.query).encode()
        ).hexdigest()
        
        # Intentar obtener conteo del caché
        total_count = None
        if use_cache:
            total_count = RecycleBinCache.get_count(filters_hash)
        
        # Si no está en caché, calcular
        if total_count is None:
            total_count = queryset.count()
            if use_cache:
                RecycleBinCache.set_count(filters_hash, total_count)
        
        # Calcular páginas
        total_pages = (total_count + page_size - 1) // page_size
        
        # Obtener elementos de la página
        offset = (page_number - 1) * page_size
        page_items = list(queryset[offset:offset + page_size])
        
        return page_items, total_count, total_pages
    
    @staticmethod
    def get_cursor_page(queryset, cursor_field, cursor_value, page_size=20, direction='next'):
        """
        Implementa paginación basada en cursor para mejor rendimiento en datasets grandes.
        
        Args:
            queryset: QuerySet a paginar
            cursor_field: Campo usado como cursor (ej: 'id', 'deleted_at')
            cursor_value: Valor del cursor
            page_size: Tamaño de página
            direction: 'next' o 'prev'
            
        Returns:
            tuple: (page_items, next_cursor, prev_cursor)
        """
        if direction == 'next':
            if cursor_value:
                queryset = queryset.filter(**{f'{cursor_field}__lt': cursor_value})
            page_items = list(queryset[:page_size + 1])
        else:  # prev
            if cursor_value:
                queryset = queryset.filter(**{f'{cursor_field}__gt': cursor_value})
            page_items = list(queryset.order_by(cursor_field)[:page_size + 1])
            page_items.reverse()
        
        has_more = len(page_items) > page_size
        if has_more:
            page_items = page_items[:page_size]
        
        next_cursor = None
        prev_cursor = None
        
        if page_items:
            if has_more and direction == 'next':
                next_cursor = getattr(page_items[-1], cursor_field)
            if cursor_value:
                prev_cursor = getattr(page_items[0], cursor_field)
        
        return page_items, next_cursor, prev_cursor
