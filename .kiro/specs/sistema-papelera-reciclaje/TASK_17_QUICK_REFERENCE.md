# Task 17: Dashboard de Papelera - Guía Rápida

## 🚀 Acceso Rápido

### URLs
```
Dashboard: /core/papelera/dashboard/
Exportar CSV: /core/papelera/exportar/?format=csv
Exportar JSON: /core/papelera/exportar/?format=json
```

### Nombres de URL Django
```python
{% url 'core:recycle_bin_dashboard' %}
{% url 'core:recycle_bin_export_report' %}
```

## 📊 Estadísticas Disponibles

### Métricas Generales
- **Total Eliminados:** Todos los elementos en el período
- **Total Restaurados:** Elementos recuperados
- **Total Pendientes:** Elementos en papelera
- **Eliminados Permanentemente:** Elementos borrados definitivamente
- **Tasa de Restauración:** Porcentaje de elementos restaurados
- **Tasa de Eliminación Permanente:** Porcentaje de eliminaciones definitivas

### Agrupaciones
1. **Por Módulo:** oficinas, bienes, catálogo, core
2. **Por Usuario:** Top 10 usuarios (solo admin)
3. **Por Tiempo:** Tendencia diaria

## 🎨 Gráficos

### 1. Elementos por Módulo
- **Tipo:** Barras agrupadas
- **Datos:** Total, restaurados, pendientes
- **Ubicación:** Superior izquierda

### 2. Restauraciones vs Eliminaciones
- **Tipo:** Dona (doughnut)
- **Datos:** Restaurados, pendientes, permanentes
- **Ubicación:** Superior derecha

### 3. Tendencia en el Tiempo
- **Tipo:** Línea con área
- **Datos:** Eliminados y restaurados por día
- **Ubicación:** Centro

### 4. Top 10 Usuarios (Admin)
- **Tipo:** Barras horizontales
- **Datos:** Total y restaurados por usuario
- **Ubicación:** Inferior

## 🔍 Filtros

### Rango de Fechas
```python
?date_range=7    # Últimos 7 días
?date_range=30   # Últimos 30 días (default)
?date_range=90   # Últimos 90 días
?date_range=365  # Último año
?date_range=0    # Todo el tiempo
```

### Exportación con Filtros
```python
# CSV con filtros
?format=csv&date_range=30&status=pending&module=oficinas

# JSON con filtros
?format=json&date_range=90&status=restored
```

## 📥 Exportación

### Formato CSV
```python
# Exportar todo
GET /core/papelera/exportar/?format=csv

# Exportar solo pendientes
GET /core/papelera/exportar/?format=csv&status=pending

# Exportar por módulo
GET /core/papelera/exportar/?format=csv&module=oficinas
```

### Formato JSON
```python
# Exportar todo
GET /core/papelera/exportar/?format=json

# Con filtros
GET /core/papelera/exportar/?format=json&date_range=7&status=restored
```

### Estructura JSON
```json
{
  "date_range_days": 30,
  "total_records": 15,
  "exported_at": "2025-01-09T10:30:00Z",
  "data": [
    {
      "id": 1,
      "module_name": "oficinas",
      "content_type": "oficina",
      "object_repr": "Oficina Central",
      "deleted_by": "admin",
      "deleted_at": "2025-01-01T10:00:00Z",
      "deletion_reason": "Reorganización",
      "status": "restored",
      "restored_by": "admin",
      "restored_at": "2025-01-05T15:30:00Z",
      "auto_delete_at": "2025-02-01T10:00:00Z"
    }
  ]
}
```

## 🔒 Permisos

### Administradores
- ✅ Ver todas las estadísticas
- ✅ Ver estadísticas por usuario
- ✅ Exportar todos los datos
- ✅ Acceder a todos los gráficos

### Usuarios Regulares
- ✅ Ver sus propias estadísticas
- ❌ No ven estadísticas de otros usuarios
- ✅ Exportar solo sus datos
- ✅ Ver gráficos de sus datos

## 💻 Código de Ejemplo

### Acceder al Dashboard en Template
```html
<a href="{% url 'core:recycle_bin_dashboard' %}" class="btn btn-info">
    <i class="fas fa-chart-line"></i> Dashboard
</a>
```

### Botón de Exportación
```html
<!-- CSV -->
<a href="{% url 'core:recycle_bin_export_report' %}?format=csv&date_range=30" 
   class="btn btn-success">
    <i class="fas fa-file-csv"></i> Exportar CSV
</a>

<!-- JSON -->
<a href="{% url 'core:recycle_bin_export_report' %}?format=json&date_range=30" 
   class="btn btn-info">
    <i class="fas fa-file-code"></i> Exportar JSON
</a>
```

### Obtener Estadísticas en Vista
```python
from apps.core.utils import RecycleBinService

# Obtener estadísticas básicas
stats = RecycleBinService.get_recycle_bin_stats(request.user)

# stats contiene:
# - total: Total de elementos
# - by_module: Dict con conteo por módulo
# - near_auto_delete: Elementos cerca de expirar
# - ready_for_auto_delete: Elementos listos para eliminar
```

### Consultas Personalizadas
```python
from apps.core.models import RecycleBin
from django.db.models import Count, Q

# Estadísticas por módulo
stats = RecycleBin.objects.values('module_name').annotate(
    total=Count('id'),
    restored=Count('id', filter=Q(restored_at__isnull=False)),
    pending=Count('id', filter=Q(restored_at__isnull=True))
)

# Estadísticas por usuario
user_stats = RecycleBin.objects.values('deleted_by__username').annotate(
    total=Count('id')
).order_by('-total')
```

## 🎯 Casos de Uso Comunes

### 1. Ver Dashboard General
```
1. Ir a Papelera de Reciclaje
2. Clic en botón "Dashboard"
3. Ver estadísticas y gráficos
```

### 2. Analizar Período Específico
```
1. Acceder al dashboard
2. Seleccionar período en el filtro (7, 30, 90 días)
3. El dashboard se actualiza automáticamente
```

### 3. Exportar Reporte
```
1. Acceder al dashboard
2. Scroll hasta "Exportar Reportes"
3. Clic en "Exportar CSV" o "Exportar JSON"
4. El archivo se descarga automáticamente
```

### 4. Identificar Elementos Próximos a Expirar
```
1. Acceder al dashboard
2. Ver alerta en la parte superior
3. Clic en "Ver elementos"
4. Se redirige a la lista filtrada
```

## 📱 Responsive

### Desktop
- Gráficos en 2 columnas
- Tablas completas
- Todos los detalles visibles

### Tablet
- Gráficos en 1 columna
- Tablas con scroll horizontal
- Estadísticas apiladas

### Mobile
- Todo en 1 columna
- Gráficos adaptados
- Navegación simplificada

## 🎨 Colores y Estilos

### Badges de Módulos
```css
.module-badge.oficinas   { background: #e3f2fd; color: #1976d2; }
.module-badge.bienes     { background: #f3e5f5; color: #7b1fa2; }
.module-badge.catalogo   { background: #e8f5e9; color: #388e3c; }
.module-badge.core       { background: #fff3e0; color: #f57c00; }
```

### Tarjetas de Estadísticas
```css
.stat-card           { gradient: purple }
.stat-card.warning   { gradient: pink-red }
.stat-card.success   { gradient: blue-cyan }
.stat-card.info      { gradient: green-cyan }
```

## 🔧 Troubleshooting

### Dashboard no muestra datos
- Verificar que hay elementos en la papelera
- Verificar el rango de fechas seleccionado
- Verificar permisos del usuario

### Exportación no funciona
- Verificar autenticación
- Verificar formato especificado (csv o json)
- Verificar que hay datos para exportar

### Gráficos no se muestran
- Verificar que Chart.js está cargado
- Verificar consola del navegador
- Verificar que hay datos disponibles

## 📚 Referencias

### Archivos Relacionados
- Vista: `apps/core/views.py` (líneas finales)
- Template: `templates/core/recycle_bin_dashboard.html`
- URLs: `apps/core/urls.py`
- Tests: `tests/test_recycle_bin_dashboard.py`

### Dependencias
- Chart.js 3.9.1 (CDN)
- Bootstrap 4/5
- Font Awesome
- Django 4.x

### Documentación Externa
- [Chart.js Docs](https://www.chartjs.org/docs/latest/)
- [Bootstrap Docs](https://getbootstrap.com/docs/)
- [Django Views](https://docs.djangoproject.com/en/stable/topics/http/views/)
