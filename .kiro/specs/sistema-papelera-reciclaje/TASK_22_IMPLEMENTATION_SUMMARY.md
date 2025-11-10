# Task 22: Reportes de Auditoría de Eliminaciones - Resumen de Implementación

## 📋 Descripción General

Se ha implementado un sistema completo de reportes de auditoría de eliminaciones con filtros avanzados, exportación a múltiples formatos, gráficos de tendencias y detección automática de patrones sospechosos.

## ✅ Componentes Implementados

### 1. Vista Principal de Reportes (`deletion_audit_reports`)

**Ubicación:** `apps/core/views.py`

**Características:**
- Filtros avanzados por usuario, acción, módulo, estado, rango de fechas y búsqueda de texto
- Estadísticas generales (total de operaciones, exitosas, fallidas)
- Estadísticas por acción y por módulo
- Top 10 usuarios con más actividad
- Gráficos de tendencias de los últimos 30 días
- Detección automática de patrones sospechosos
- Paginación de resultados (50 por página)
- Segregación de datos según permisos de usuario

**Filtros Disponibles:**
- Usuario (búsqueda por nombre)
- Acción (soft_delete, restore, permanent_delete, etc.)
- Módulo (oficinas, bienes, catálogo)
- Estado (exitoso/fallido)
- Fecha desde/hasta
- Búsqueda de texto en objeto, motivo y mensajes de error

### 2. Detección de Patrones Sospechosos

**Función:** `_detect_suspicious_patterns()`

**Patrones Detectados:**

1. **Múltiples Eliminaciones Permanentes** (Alta Severidad)
   - Umbral: 5+ eliminaciones permanentes en 1 hora
   - Icono: ⚠️

2. **Múltiples Intentos Fallidos** (Media Severidad)
   - Umbral: 3+ operaciones fallidas en 1 hora
   - Icono: ⚡

3. **Eliminaciones Masivas** (Alta Severidad)
   - Umbral: 20+ eliminaciones en un módulo en 24 horas
   - Icono: 🔥

4. **Actividad Fuera de Horario** (Baja Severidad)
   - Horario: 10pm - 6am
   - Umbral: 5+ operaciones
   - Icono: 🌙

5. **Restaurar y Eliminar Permanentemente** (Media Severidad)
   - Umbral: 3+ restauraciones seguidas de 3+ eliminaciones permanentes
   - Icono: 🔄

### 3. Exportación de Reportes

**Vista:** `deletion_audit_export`

**Formatos Soportados:**

#### A. Exportación a Excel
- Librería: `openpyxl`
- Características:
  - Hoja principal con todos los logs filtrados
  - Hoja de estadísticas con resúmenes
  - Formato profesional con colores y estilos
  - Columnas ajustadas automáticamente
  - Límite: 10,000 registros

**Columnas Exportadas:**
- Fecha/Hora
- Usuario
- Acción
- Módulo
- Objeto
- Exitoso
- Motivo
- IP
- Código de Seguridad

#### B. Exportación a PDF
- Librería: `reportlab`
- Características:
  - Orientación horizontal para más espacio
  - Título y metadatos del reporte
  - Estadísticas generales
  - Estadísticas por acción
  - Detalle de primeras 100 operaciones
  - Formato profesional con tablas y colores

### 4. Vista de Detalle de Auditoría

**Vista:** `deletion_audit_detail`

**Información Mostrada:**
- Información general (acción, usuario, fecha, módulo, objeto, estado)
- Información de contexto (IP, User Agent, motivo, código de seguridad)
- Snapshot completo del objeto antes de la operación
- Estado anterior (para restauraciones)
- Metadatos adicionales
- Operaciones relacionadas del mismo objeto (últimas 10)
- Enlace a la entrada en papelera (si existe)

### 5. Comando de Management para Alertas Automáticas

**Comando:** `check_suspicious_patterns`

**Uso:**
```bash
# Analizar últimas 24 horas (por defecto)
python manage.py check_suspicious_patterns

# Analizar últimas 48 horas
python manage.py check_suspicious_patterns --hours 48

# Enviar notificaciones a administradores
python manage.py check_suspicious_patterns --send-notifications

# Modo verbose con detalles
python manage.py check_suspicious_patterns --verbose --send-notifications
```

**Características:**
- Análisis configurable de período de tiempo
- Detección de 6 tipos de patrones sospechosos
- Envío automático de notificaciones a administradores
- Clasificación por severidad (alta, media, baja)
- Modo verbose para debugging

## 🎨 Templates Creados

### 1. `deletion_audit_reports.html`
- Diseño responsive y moderno
- Tarjetas de estadísticas con iconos
- Alertas visuales para patrones sospechosos con colores por severidad
- Gráfico interactivo de tendencias con Chart.js
- Formulario de filtros intuitivo
- Botones de exportación destacados
- Tabla de logs con badges de estado
- Paginación completa

### 2. `deletion_audit_detail.html`
- Layout de 2 columnas para información general y contexto
- Visualización de JSON formateado para snapshots
- Tabla de operaciones relacionadas
- Navegación fácil entre logs relacionados
- Diseño limpio y profesional

## 🔗 URLs Agregadas

```python
# Auditoría de Eliminaciones
path('auditoria/eliminaciones/', views.deletion_audit_reports, name='deletion_audit_reports'),
path('auditoria/eliminaciones/exportar/', views.deletion_audit_export, name='deletion_audit_export'),
path('auditoria/eliminaciones/<int:log_id>/', views.deletion_audit_detail, name='deletion_audit_detail'),
```

## 🧪 Tests Implementados

**Archivo:** `tests/test_deletion_audit_reports.py`

**Cobertura de Tests:**

1. **DeletionAuditReportsViewTest** (8 tests)
   - Autenticación y permisos
   - Visualización de estadísticas
   - Filtros por usuario, acción, fecha
   - Funcionalidad de búsqueda

2. **SuspiciousPatternDetectionTest** (3 tests)
   - Detección de eliminaciones permanentes masivas
   - Detección de eliminaciones masivas por módulo
   - Detección de múltiples fallos

3. **AuditExportTest** (4 tests)
   - Autenticación y permisos para exportación
   - Exportación a Excel
   - Exportación a PDF
   - Aplicación de filtros en exportación

4. **AuditDetailViewTest** (4 tests)
   - Autenticación requerida
   - Visualización de información del log
   - Visualización de logs relacionados
   - Visualización de snapshots

5. **TrendDataTest** (1 test)
   - Datos de tendencias de últimos 30 días

**Total:** 20 tests completos

## 📊 Gráficos y Visualizaciones

### Gráfico de Tendencias
- Librería: Chart.js 3.9.1
- Tipo: Líneas múltiples
- Datos: Últimos 30 días
- Series: Una por cada tipo de acción
- Colores diferenciados por acción
- Interactivo con tooltips
- Responsive

### Estadísticas Visuales
- Tarjetas con iconos descriptivos
- Colores semánticos (éxito/error)
- Badges para estados y acciones
- Alertas visuales para patrones sospechosos

## 🔒 Seguridad y Permisos

**Permisos Requeridos:**
- Vista principal: `can_view_deletion_audit_logs`
- Exportación: `can_view_deletion_audit_logs`
- Detalle: `can_view_deletion_audit_logs`

**Roles con Acceso:**
- Administrador: Acceso completo
- Auditor: Acceso completo de solo lectura

**Segregación de Datos:**
- Los filtros respetan los permisos del usuario
- Los patrones sospechosos se muestran según el rol

## 📦 Dependencias Requeridas

### Para Exportación a Excel:
```bash
pip install openpyxl
```

### Para Exportación a PDF:
```bash
pip install reportlab
```

**Nota:** El sistema maneja gracefully la ausencia de estas librerías, mostrando mensajes informativos al usuario.

## 🚀 Uso del Sistema

### 1. Acceder a Reportes
```
URL: /core/auditoria/eliminaciones/
```

### 2. Aplicar Filtros
- Usar el formulario de filtros en la parte superior
- Los filtros se pueden combinar
- Click en "Aplicar Filtros"

### 3. Exportar Reportes
- Click en "📊 Exportar a Excel" o "📄 Exportar a PDF"
- Los filtros activos se aplican a la exportación
- El archivo se descarga automáticamente

### 4. Ver Detalle de un Log
- Click en "Ver Detalle" en cualquier fila de la tabla
- Se muestra toda la información del log
- Se pueden ver logs relacionados del mismo objeto

### 5. Configurar Alertas Automáticas
```bash
# Agregar a crontab para ejecución cada hora
0 * * * * cd /path/to/project && python manage.py check_suspicious_patterns --send-notifications
```

## 📈 Métricas y Estadísticas

El sistema proporciona las siguientes métricas:

1. **Generales:**
   - Total de operaciones
   - Operaciones exitosas
   - Operaciones fallidas

2. **Por Acción:**
   - Conteo de cada tipo de acción
   - Ordenado por frecuencia

3. **Por Módulo:**
   - Conteo por módulo (oficinas, bienes, catálogo)
   - Ordenado por frecuencia

4. **Por Usuario:**
   - Top 10 usuarios más activos
   - Conteo de operaciones por usuario

5. **Tendencias:**
   - Evolución diaria de operaciones
   - Últimos 30 días
   - Desglosado por tipo de acción

## 🎯 Patrones Sospechosos - Detalles

### Configuración de Umbrales

Los umbrales son configurables en el código:

```python
# En _detect_suspicious_patterns()
permanent_deletes_threshold = 5  # en 1 hora
failures_threshold = 3  # en 1 hora
massive_deletes_threshold = 20  # en 24 horas
off_hours_operations_threshold = 5
restore_delete_threshold = 3  # de cada tipo
```

### Niveles de Severidad

- **Alta (high):** Requiere atención inmediata
  - Múltiples eliminaciones permanentes
  - Eliminaciones masivas
  - Uso excesivo del código de seguridad

- **Media (medium):** Requiere revisión
  - Múltiples intentos fallidos
  - Patrón de restaurar y eliminar

- **Baja (low):** Informativo
  - Actividad fuera de horario laboral

## 🔧 Personalización

### Agregar Nuevos Patrones

Para agregar un nuevo patrón sospechoso:

1. Editar `_detect_suspicious_patterns()` en `views.py`
2. Agregar lógica de detección
3. Agregar al array `patterns` con estructura:
```python
{
    'type': 'pattern_type',
    'severity': 'high|medium|low',
    'message': 'Descripción del patrón',
    'icon': '🔥',
    'user': 'username',
    'count': 10,
    'details': {...}
}
```

### Personalizar Exportación

Los métodos `_export_to_excel()` y `_export_to_pdf()` pueden ser personalizados para:
- Agregar más columnas
- Cambiar estilos
- Agregar más hojas/páginas
- Incluir gráficos

## 📝 Notas de Implementación

1. **Performance:**
   - Queries optimizadas con `select_related()`
   - Índices en campos de búsqueda frecuente
   - Paginación para grandes volúmenes
   - Límite de 10,000 registros en exportación

2. **Compatibilidad:**
   - Funciona sin librerías de exportación (muestra mensaje)
   - Responsive design para móviles
   - Compatible con todos los navegadores modernos

3. **Mantenibilidad:**
   - Código bien documentado
   - Funciones separadas por responsabilidad
   - Tests completos
   - Fácil de extender

## ✅ Verificación de Requisitos

- ✅ Implementar vista de reportes de auditoría con filtros avanzados
- ✅ Crear exportación de logs de auditoría a PDF y Excel
- ✅ Agregar gráficos de tendencias de eliminaciones por período
- ✅ Implementar alertas automáticas para patrones sospechosos
- ✅ Requirements 6.4, 6.1 cumplidos

## 🎉 Conclusión

El sistema de reportes de auditoría de eliminaciones está completamente implementado y probado. Proporciona una herramienta poderosa para:
- Monitorear todas las operaciones de eliminación
- Detectar comportamientos anómalos
- Generar reportes profesionales
- Mantener la seguridad del sistema
- Cumplir con requisitos de auditoría

El sistema es extensible, bien documentado y listo para producción.
