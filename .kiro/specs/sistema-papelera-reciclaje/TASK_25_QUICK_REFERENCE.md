# Task 25: Guía Rápida de Uso - Integración de Papelera en Navegación

## Para Desarrolladores

### Agregar Acceso Rápido en un Nuevo Módulo

```django
{% extends 'base.html' %}
{% load recycle_bin_quick_access %}

{% block content %}
<div class="container">
    <!-- Agregar acceso rápido al inicio del listado -->
    {% recycle_bin_quick_access 'nombre_modulo' %}
    
    <!-- Resto del contenido -->
    ...
</div>
{% endblock %}
```

### Usar Badge en Encabezados

```django
<h1>
    Mi Módulo
    {% recycle_bin_module_badge 'nombre_modulo' %}
</h1>
```

### Agregar Widget de Notificaciones

```django
{% load recycle_bin_quick_access %}

<!-- En dashboard o página principal -->
{% recycle_bin_notification_widget %}
```

### Acceder a Variables Globales

En cualquier template:
```django
{% if can_view_recycle_bin %}
    <p>Elementos en papelera: {{ recycle_bin_count }}</p>
    <p>Próximos a eliminarse: {{ recycle_bin_near_delete_count }}</p>
{% endif %}
```

### Usar API de JavaScript

```javascript
// Actualizar contadores manualmente
window.RecycleBinNotifications.updateCounters();

// Mostrar notificación personalizada
window.RecycleBinNotifications.showNotification(
    'Título',
    'Mensaje',
    'warning' // info, success, warning, danger
);

// Configurar opciones
window.RecycleBinNotifications.config.updateInterval = 120000; // 2 minutos
window.RecycleBinNotifications.config.enableSound = true;
```

### Llamar API Endpoint

```javascript
fetch('/api/recycle-bin/status/')
    .then(response => response.json())
    .then(data => {
        console.log('Total:', data.count);
        console.log('Urgentes:', data.near_delete_count);
        console.log('Por módulo:', data.module_stats);
    });
```

## Para Administradores

### Verificar Funcionamiento

1. **Navegación Principal**:
   - Buscar enlace "Papelera" con icono de papelera
   - Verificar badges azul (total) y rojo (urgentes)

2. **Banner de Advertencia**:
   - Aparece cuando hay elementos próximos a eliminarse
   - Puede cerrarse con la X
   - Enlace directo a elementos urgentes

3. **Listados de Módulos**:
   - Alert box azul al inicio si hay elementos en papelera
   - Botón "Ver en papelera" filtra por módulo

4. **Dashboard**:
   - Widget con elementos más urgentes
   - Muestra días restantes con colores:
     - Rojo: 0-1 días
     - Amarillo: 2-3 días
     - Azul: 4-7 días

### Solución de Problemas

**No veo el enlace de papelera**:
- Verificar que el usuario tenga rol administrador, funcionario o auditor
- Verificar que `can_view_recycle_bin` sea True en el perfil

**Los contadores no se actualizan**:
- Verificar que JavaScript esté cargado (ver consola del navegador)
- Verificar que el endpoint `/api/recycle-bin/status/` responda
- Revisar permisos del usuario

**Accesos rápidos no aparecen**:
- Verificar que haya elementos en papelera para ese módulo
- Verificar que el template tag esté cargado
- Revisar permisos del usuario

## Configuración

### Variables de Entorno

No requiere configuración adicional. Usa las variables existentes:
- `RECYCLE_BIN_RETENTION_DAYS`: Días de retención
- `RECYCLE_BIN_AUTO_CLEANUP_ENABLED`: Limpieza automática

### Personalización de JavaScript

Editar `static/js/recycle_bin_notifications.js`:

```javascript
const CONFIG = {
    updateInterval: 60000,      // Frecuencia de actualización (ms)
    apiEndpoint: '/api/...',    // Endpoint de API
    enableNotifications: true,   // Mostrar notificaciones toast
    enableSound: false,          // Reproducir sonido
};
```

## Permisos

### Roles y Acceso

| Rol | Ver Papelera | Ver Todos | Notificaciones |
|-----|--------------|-----------|----------------|
| Administrador | ✅ | ✅ | ✅ |
| Funcionario | ✅ | ❌ (solo propios) | ✅ |
| Auditor | ✅ | ✅ | ✅ |
| Consulta | ❌ | ❌ | ❌ |

### Métodos de Verificación

```python
# En vistas
if request.user.profile.can_view_recycle_bin():
    # Usuario puede ver papelera
    pass

# En templates
{% if can_view_recycle_bin %}
    <!-- Mostrar elementos de papelera -->
{% endif %}
```

## Ejemplos de Uso

### Ejemplo 1: Módulo Personalizado

```django
{% extends 'base.html' %}
{% load recycle_bin_quick_access %}

{% block content %}
<div class="container">
    <h1>
        Mi Módulo Personalizado
        {% recycle_bin_module_badge 'mi_modulo' %}
    </h1>
    
    {% recycle_bin_quick_access 'mi_modulo' %}
    
    <!-- Listado del módulo -->
    <table class="table">
        ...
    </table>
</div>
{% endblock %}
```

### Ejemplo 2: Dashboard Personalizado

```django
{% extends 'base.html' %}
{% load recycle_bin_quick_access %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-8">
            <!-- Contenido principal -->
        </div>
        <div class="col-md-4">
            <!-- Widget de notificaciones -->
            {% recycle_bin_notification_widget %}
        </div>
    </div>
</div>
{% endblock %}
```

### Ejemplo 3: Notificación Personalizada

```javascript
// Después de eliminar un elemento
document.getElementById('deleteBtn').addEventListener('click', function() {
    // ... código de eliminación ...
    
    // Mostrar notificación
    window.RecycleBinNotifications.showNotification(
        'Elemento Eliminado',
        'El elemento se movió a la papelera de reciclaje',
        'success'
    );
    
    // Actualizar contadores
    window.RecycleBinNotifications.updateCounters();
});
```

## Mantenimiento

### Logs a Monitorear

1. **Errores de API**:
   ```
   Error actualizando contadores de papelera: ...
   ```

2. **Errores de JavaScript**:
   - Abrir consola del navegador (F12)
   - Buscar errores relacionados con RecycleBinNotifications

### Optimización

Si el sistema tiene muchos elementos en papelera:

1. **Agregar Caché**:
   ```python
   from django.core.cache import cache
   
   def recycle_bin_context(request):
       cache_key = f'recycle_bin_count_{request.user.id}'
       count = cache.get(cache_key)
       
       if count is None:
           count = RecycleBin.objects.filter(...).count()
           cache.set(cache_key, count, 300)  # 5 minutos
       
       return {'recycle_bin_count': count}
   ```

2. **Aumentar Intervalo de Actualización**:
   ```javascript
   CONFIG.updateInterval = 300000; // 5 minutos
   ```

## Soporte

Para problemas o preguntas:
1. Revisar logs de Django
2. Verificar consola del navegador
3. Revisar permisos de usuario
4. Consultar documentación completa en TASK_25_IMPLEMENTATION_SUMMARY.md
