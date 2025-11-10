"""
Parche para agregar invalidación de caché a RecycleBinService.
Este archivo debe ser integrado en utils.py
"""

# Agregar al inicio de cada método de RecycleBinService que modifique datos:

# En soft_delete_object, después de crear recycle_entry:
"""
                # Invalidar caché
                from .cache_utils import RecycleBinCache
                RecycleBinCache.invalidate_user(user.id)
                RecycleBinCache.invalidate_module(module_name)
"""

# En restore_object, después de marcar como restaurado:
"""
                # Invalidar caché
                from .cache_utils import RecycleBinCache
                RecycleBinCache.invalidate_user(user.id)
                RecycleBinCache.invalidate_module(recycle_entry.module_name)
"""

# En permanent_delete, después de eliminar:
"""
                # Invalidar caché
                from .cache_utils import RecycleBinCache
                RecycleBinCache.invalidate_user(user.id)
                RecycleBinCache.invalidate_module(recycle_entry.module_name)
"""

# En auto_cleanup, después del loop:
"""
            # Invalidar todo el caché después de la limpieza
            from .cache_utils import RecycleBinCache
            RecycleBinCache.invalidate_all()
"""
