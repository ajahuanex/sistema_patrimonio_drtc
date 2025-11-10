# Referencia Rápida - Filtros de Papelera de Reciclaje

## Filtros Disponibles

### 🔍 Búsqueda por Texto
```
Campo: search
Busca en: Nombre del objeto, Motivo de eliminación
Ejemplo: ?search=laptop
```

### 📦 Filtro por Módulo
```
Campo: module
Valores: oficinas, bienes, catalogo, core
Ejemplo: ?module=oficinas
```

### ⏰ Filtro por Tiempo Restante
```
Campo: time_remaining
Valores:
  - expired: Listos para eliminar (0 días)
  - critical: Crítico (1-3 días)
  - warning: Advertencia (4-7 días)
  - normal: Normal (8-14 días)
  - safe: Seguro (más de 14 días)
Ejemplo: ?time_remaining=critical
```

### 📊 Filtro por Estado
```
Campo: status
Valores: active, restored
Ejemplo: ?status=active
```

### 📅 Filtro por Rango de Fechas
```
Campos: date_from, date_to
Formato: YYYY-MM-DD
Ejemplo: ?date_from=2025-01-01&date_to=2025-01-31
```

### 👤 Filtro por Usuario (Solo Admin)
```
Campo: deleted_by
Busca en: Username, Nombre, Apellido
Ejemplo: ?deleted_by=admin
```

## Combinaciones Comunes

### Elementos Urgentes
```
?time_remaining=critical
```

### Mis Eliminaciones Recientes
```
?deleted_by=<mi_usuario>&date_from=<hace_7_dias>
```

### Bienes Próximos a Expirar
```
?module=bienes&time_remaining=warning
```

### Búsqueda con Filtros
```
?search=laptop&module=bienes&time_remaining=safe
```

### Auditoría de Usuario
```
?deleted_by=usuario&date_from=2025-01-01&date_to=2025-01-31
```

## Códigos de Color

### Tiempo Restante
- 🔴 **Rojo**: 0-3 días (urgente)
- 🟡 **Amarillo**: 4-7 días (advertencia)
- 🔵 **Azul**: 8-14 días (normal)
- 🟢 **Verde**: 15+ días (seguro)

### Estado
- 🔵 **Azul**: En papelera
- 🔴 **Rojo**: Listo para eliminar
- 🟡 **Amarillo**: Próximo a eliminar
- 🟢 **Verde**: Restaurado

## Atajos de Teclado (Futuros)

```
Ctrl + F: Enfocar búsqueda
Ctrl + L: Limpiar filtros
Ctrl + 1: Filtro críticos
Ctrl + 2: Filtro advertencia
Ctrl + M: Mis eliminaciones
```

## API de Filtros (Para Desarrolladores)

### Aplicar Filtros Programáticamente

```python
from apps.core.filters import RecycleBinFilterForm

# Crear formulario con datos
form = RecycleBinFilterForm(data={
    'module': 'oficinas',
    'time_remaining': 'critical',
    'search': 'test'
})

# Validar y aplicar
if form.is_valid():
    queryset = RecycleBin.objects.all()
    filtered = form.apply_filters(queryset, user)
```

### Usar Filtros Rápidos

```python
from apps.core.filters import RecycleBinQuickFilters

queryset = RecycleBin.objects.all()

# Elementos próximos a expirar
expiring = RecycleBinQuickFilters.get_expiring_soon(queryset)

# Elementos expirados
expired = RecycleBinQuickFilters.get_expired(queryset)

# Por usuario
user_items = RecycleBinQuickFilters.get_by_user(queryset, user)
```

### Template Tags

```django
{% load recycle_bin_tags %}

<!-- Preservar parámetros GET -->
<a href="{% url_replace request page=2 %}">Página 2</a>

<!-- Badge de tiempo restante -->
{% time_remaining_badge entry %}

<!-- Badge de estado -->
{% status_badge entry %}

<!-- Clase de badge según días -->
{{ days|get_time_remaining_badge_class }}

<!-- Icono según días -->
<i class="fas {{ days|get_time_remaining_icon }}"></i>
```

## Estadísticas de Uso

### Contadores Disponibles
```python
stats = {
    'total': Total de elementos,
    'near_auto_delete': Próximos a eliminar (7 días),
    'ready_for_auto_delete': Listos para eliminar,
    'by_module': Distribución por módulo
}
```

### Quick Filters
```python
quick_filters = {
    'expiring_soon': Elementos en 7 días,
    'expired': Elementos expirados,
    'my_deletions': Mis eliminaciones
}
```

## Troubleshooting

### Problema: No aparecen resultados
**Solución**: Verificar filtros activos, limpiar y buscar nuevamente

### Problema: Filtros no se aplican
**Solución**: Click en "Aplicar Filtros", verificar validación

### Problema: Paginación pierde filtros
**Solución**: Reportar bug, debería preservarse automáticamente

### Problema: No veo filtro de usuario
**Solución**: Solo disponible para administradores

## Mejores Prácticas

1. ✅ Usar filtros rápidos para tareas comunes
2. ✅ Combinar filtros para búsquedas específicas
3. ✅ Limpiar filtros antes de nueva búsqueda
4. ✅ Guardar URLs con filtros frecuentes
5. ✅ Revisar resumen de filtros activos

## Recursos

- **Documentación completa**: TASK_11_USAGE_GUIDE.md
- **Verificación técnica**: TASK_11_VERIFICATION.md
- **Resumen ejecutivo**: TASK_11_SUMMARY.md
- **Código fuente**: apps/core/filters.py
- **Tests**: tests/test_recycle_bin_filters.py
