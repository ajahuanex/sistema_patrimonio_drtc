# Mejoras en el Sistema de Importación

## 📋 Resumen de Cambios

Se han implementado mejoras significativas en el sistema de importación de datos para Catálogo y Bienes Patrimoniales, enfocadas en:

1. **Manejo flexible de duplicados en denominación**
2. **Sistema de observaciones para revisión posterior**
3. **Indicadores visuales de carga durante la importación**
4. **Validación mejorada para bienes patrimoniales**

---

## 🆕 Nuevo Modelo: ImportObservation

### Descripción
Modelo para registrar observaciones durante la importación de datos, permitiendo continuar con el proceso incluso cuando hay problemas menores que requieren revisión posterior.

### Ubicación
`apps/catalogo/models.py`

### Características

**Tipos de Observaciones:**
- `duplicado_denominacion`: Denominación Duplicada
- `dato_incompleto`: Dato Incompleto
- `formato_invalido`: Formato Inválido
- `referencia_faltante`: Referencia Faltante
- `otro`: Otro

**Niveles de Severidad:**
- `info`: Información
- `warning`: Advertencia
- `error`: Error

**Módulos Soportados:**
- `catalogo`: Catálogo
- `bienes`: Bienes Patrimoniales
- `oficinas`: Oficinas

### Campos Principales

```python
- modulo: Módulo donde se generó la observación
- tipo: Tipo de problema detectado
- severidad: Nivel de severidad
- fila_excel: Número de fila en el archivo Excel
- campo: Campo que generó la observación
- valor_original: Valor original del campo
- valor_procesado: Valor después del procesamiento
- mensaje: Descripción detallada
- datos_adicionales: Información adicional en JSON
- fecha_importacion: Fecha y hora de la importación
- usuario: Usuario que realizó la importación
- archivo_nombre: Nombre del archivo importado
- resuelto: Si la observación fue revisada
- resuelto_por: Usuario que resolvió
- fecha_resolucion: Fecha de resolución
- notas_resolucion: Notas sobre la resolución
```

### Métodos Útiles

```python
# Crear observación
ImportObservation.crear_observacion(
    modulo='catalogo',
    tipo='duplicado_denominacion',
    fila_excel=10,
    campo='Denominación',
    mensaje='Denominación duplicada encontrada',
    usuario=request.user,
    archivo_nombre='catalogo_2025.xlsx'
)

# Obtener pendientes
observaciones = ImportObservation.obtener_pendientes(modulo='catalogo')

# Marcar como resuelto
observacion.marcar_como_resuelto(usuario=request.user, notas='Revisado y aprobado')

# Obtener por archivo
observaciones = ImportObservation.obtener_por_archivo('catalogo_2025.xlsx')
```

---

## 📊 Mejoras en Importación de Catálogo

### 1. Manejo de Duplicados en Denominación

**Comportamiento Anterior:**
- Rechazaba registros con denominación duplicada
- Detenía la importación

**Comportamiento Nuevo:**
- Permite continuar con la importación (configurable)
- Registra observación para revisión posterior
- Parámetro `permitir_duplicados_denominacion` (default: `True`)

### 2. Actualización de CatalogoImporter

**Nuevos Parámetros del Constructor:**
```python
CatalogoImporter(
    usuario=None,  # Usuario que realiza la importación
    archivo_nombre='',  # Nombre del archivo
    permitir_duplicados_denominacion=True  # Permitir duplicados
)
```

**Nuevos Atributos:**
```python
self.observaciones = []  # Lista de observaciones generadas
```

**Reporte Mejorado:**
```python
{
    'exito': True/False,
    'registros_procesados': 100,
    'registros_creados': 80,
    'registros_actualizados': 20,
    'errores': [],
    'warnings': [],
    'observaciones': [],  # NUEVO
    'total_observaciones': 5,  # NUEVO
    'resumen': 'Procesados: 100, Creados: 80, ..., Observaciones: 5'
}
```

### 3. Ejemplo de Uso

```python
from apps.catalogo.utils import importar_catalogo_desde_excel

resultado = importar_catalogo_desde_excel(
    archivo_path='/path/to/catalogo.xlsx',
    actualizar_existentes=True,
    usuario=request.user,
    archivo_nombre='catalogo_2025.xlsx',
    permitir_duplicados_denominacion=True  # Permitir duplicados
)

# Revisar observaciones
for obs in resultado['observaciones']:
    print(f"Fila {obs.fila_excel}: {obs.mensaje}")
```

---

## 🏢 Mejoras en Importación de Bienes

### 1. Validación de Denominación Duplicada

**Nueva Funcionalidad:**
- Detecta cuando hay múltiples catálogos con denominación similar
- Registra observación con todos los catálogos encontrados
- Usa el primer catálogo encontrado
- Informa al usuario sobre la ambigüedad

### 2. Detección de Coincidencias Parciales

**Comportamiento:**
- Si no hay coincidencia exacta, busca por primera palabra
- Registra observación indicando coincidencia parcial
- Permite continuar con la importación

### 3. Actualización de BienPatrimonialImporter

**Nuevos Parámetros del Constructor:**
```python
BienPatrimonialImporter(
    usuario=None,
    archivo_nombre='',
    permitir_duplicados_denominacion=True
)
```

**Nuevos Atributos:**
```python
self.observaciones = []
```

**Reporte Mejorado:**
```python
{
    'exito': True/False,
    'registros_procesados': 500,
    'registros_creados': 450,
    'registros_actualizados': 50,
    'qr_generados': 450,
    'errores': [],
    'warnings': [],
    'observaciones': [],  # NUEVO
    'total_observaciones': 15,  # NUEVO
    'resumen': 'Procesados: 500, ..., Observaciones: 15'
}
```

### 4. Tipos de Observaciones en Bienes

**Duplicado de Denominación:**
```json
{
    "tipo": "duplicado_denominacion",
    "mensaje": "Se encontraron 3 catálogos con denominación similar...",
    "datos_adicionales": {
        "codigo_patrimonial": "PAT001",
        "catalogos_encontrados": [
            {"codigo": "04220001", "denominacion": "TRACTOR AGRICOLA"},
            {"codigo": "04220002", "denominacion": "TRACTOR AGRICOLA GRANDE"}
        ],
        "catalogo_usado": "04220001"
    }
}
```

**Referencia Faltante:**
```json
{
    "tipo": "referencia_faltante",
    "mensaje": "No se encontró coincidencia exacta. Se usó coincidencia parcial...",
    "datos_adicionales": {
        "codigo_patrimonial": "PAT002",
        "catalogo_usado": "05220001",
        "tipo_coincidencia": "parcial"
    }
}
```

### 5. Ejemplo de Uso

```python
from apps.bienes.utils import importar_bienes_desde_excel

resultado = importar_bienes_desde_excel(
    archivo_path='/path/to/bienes.xlsx',
    actualizar_existentes=False,
    usuario=request.user,
    archivo_nombre='bienes_2025.xlsx',
    permitir_duplicados_denominacion=True
)

# Revisar observaciones
for obs in resultado['observaciones']:
    if obs.severidad == 'warning':
        print(f"⚠️ Fila {obs.fila_excel}: {obs.mensaje}")
```

---

## 🎨 Indicadores de Carga

### Implementación

Se agregaron indicadores visuales de carga en ambos templates de importación:

**Características:**
- Overlay de pantalla completa
- Spinner animado
- Mensaje informativo
- Barra de progreso animada
- Previene cierre accidental de la página

### Ubicación
- `templates/catalogo/importar.html`
- `templates/bienes/importar.html`

### Componentes

**HTML:**
```html
<div id="loading-overlay" style="display: none;">
    <div class="loading-content">
        <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Cargando...</span>
        </div>
        <h4 class="mt-3">Procesando importación...</h4>
        <p class="text-muted">Por favor espere...</p>
        <div class="progress mt-3">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 100%"></div>
        </div>
    </div>
</div>
```

**CSS:**
```css
#loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.8);
    z-index: 9999;
    display: flex;
    justify-content: center;
    align-items: center;
}

.loading-content {
    background: white;
    padding: 40px;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

**JavaScript:**
```javascript
$('#form-importar').on('submit', function(e) {
    if (!confirm('¿Está seguro...?')) {
        e.preventDefault();
        return false;
    }
    
    // Mostrar indicador de carga
    $('#loading-overlay').fadeIn();
    $('#btn-importar').prop('disabled', true);
    
    return true;
});
```

---

## 🔧 Admin de Observaciones

### Características

**Vista de Lista:**
- Badges de colores por módulo, tipo y severidad
- Filtros por módulo, tipo, severidad, estado
- Búsqueda por mensaje, campo, archivo
- Ordenamiento por fecha y fila
- Jerarquía de fechas

**Acciones en Lote:**
- Marcar como resuelto
- Marcar como pendiente

**Permisos:**
- No se pueden crear manualmente
- Solo superusuarios pueden eliminar

**Colores:**
- Módulos: Azul (catálogo), Verde (bienes), Morado (oficinas)
- Severidad: Azul (info), Naranja (warning), Rojo (error)
- Estado: Verde (resuelto), Naranja (pendiente)

---

## 📝 Migración

### Archivo
`apps/catalogo/migrations/0003_importobservation.py`

### Aplicar Migración

```bash
# Desarrollo
python manage.py makemigrations
python manage.py migrate

# Producción (Docker)
docker-compose exec web python manage.py migrate
```

---

## 🚀 Flujo de Trabajo Recomendado

### 1. Importación con Observaciones

```python
# Importar permitiendo duplicados
resultado = importar_catalogo_desde_excel(
    archivo_path=temp_path,
    actualizar_existentes=True,
    usuario=request.user,
    archivo_nombre=archivo.name,
    permitir_duplicados_denominacion=True
)

# Mostrar resumen
if resultado['exito']:
    messages.success(request, resultado['resumen'])
    
    # Alertar sobre observaciones
    if resultado['total_observaciones'] > 0:
        messages.warning(
            request,
            f"Se generaron {resultado['total_observaciones']} observaciones "
            f"que requieren revisión. Consulte el panel de administración."
        )
```

### 2. Revisión de Observaciones

```python
# En el admin o en una vista personalizada
from apps.catalogo.models import ImportObservation

# Obtener pendientes
pendientes = ImportObservation.obtener_pendientes(modulo='catalogo')

# Filtrar por severidad
criticas = pendientes.filter(severidad='error')
advertencias = pendientes.filter(severidad='warning')

# Revisar y resolver
for obs in criticas:
    # Revisar datos
    print(f"Fila {obs.fila_excel}: {obs.mensaje}")
    print(f"Datos: {obs.datos_adicionales}")
    
    # Marcar como resuelto
    obs.marcar_como_resuelto(
        usuario=request.user,
        notas='Revisado: denominación duplicada es correcta'
    )
```

### 3. Reportes de Observaciones

```python
# Obtener estadísticas
from django.db.models import Count

stats = ImportObservation.objects.values('tipo', 'severidad').annotate(
    total=Count('id')
).order_by('-total')

# Por archivo
archivo_stats = ImportObservation.objects.filter(
    archivo_nombre='catalogo_2025.xlsx'
).values('tipo').annotate(total=Count('id'))
```

---

## ✅ Beneficios

### 1. Flexibilidad
- No se detiene la importación por duplicados menores
- Permite revisión posterior
- Configurable según necesidades

### 2. Trazabilidad
- Registro completo de todas las observaciones
- Información detallada para auditoría
- Historial de resoluciones

### 3. Experiencia de Usuario
- Indicadores visuales claros
- Feedback inmediato
- Proceso más fluido

### 4. Mantenibilidad
- Observaciones centralizadas
- Fácil de consultar y resolver
- Reportes automáticos

---

## 📊 Casos de Uso

### Caso 1: Catálogo con Denominaciones Similares

**Escenario:**
Importar catálogo donde varios bienes tienen denominaciones muy similares (ej: "COMPUTADORA PERSONAL", "COMPUTADORA PERSONAL PORTATIL")

**Solución:**
- Importación continúa
- Se registra observación por cada duplicado
- Administrador revisa y decide si mantener o corregir

### Caso 2: Bienes con Referencias Ambiguas

**Escenario:**
Importar bienes donde la denominación coincide con múltiples catálogos

**Solución:**
- Sistema usa el primer catálogo encontrado
- Registra observación con todas las opciones
- Usuario puede corregir manualmente si es necesario

### Caso 3: Importación Masiva

**Escenario:**
Importar 10,000 registros con algunos problemas menores

**Solución:**
- Importación completa sin interrupciones
- Indicador de carga mantiene informado al usuario
- Observaciones se revisan después en lote

---

## 🔍 Consultas Útiles

### SQL para Análisis

```sql
-- Observaciones por tipo
SELECT tipo, COUNT(*) as total
FROM catalogo_importobservation
WHERE resuelto = FALSE
GROUP BY tipo
ORDER BY total DESC;

-- Observaciones por archivo
SELECT archivo_nombre, COUNT(*) as total, 
       SUM(CASE WHEN resuelto THEN 1 ELSE 0 END) as resueltos
FROM catalogo_importobservation
GROUP BY archivo_nombre
ORDER BY total DESC;

-- Observaciones críticas pendientes
SELECT * FROM catalogo_importobservation
WHERE severidad = 'error' AND resuelto = FALSE
ORDER BY fecha_importacion DESC;
```

### Django ORM

```python
# Observaciones no resueltas por usuario
from django.db.models import Count
ImportObservation.objects.filter(
    resuelto=False
).values('usuario__username').annotate(
    total=Count('id')
).order_by('-total')

# Observaciones de la última semana
from datetime import timedelta
from django.utils import timezone
ultima_semana = timezone.now() - timedelta(days=7)
ImportObservation.objects.filter(
    fecha_importacion__gte=ultima_semana
).count()

# Tasa de resolución
total = ImportObservation.objects.count()
resueltos = ImportObservation.objects.filter(resuelto=True).count()
tasa = (resueltos / total * 100) if total > 0 else 0
print(f"Tasa de resolución: {tasa:.2f}%")
```

---

## 🎯 Próximos Pasos Recomendados

1. **Vista Personalizada de Observaciones**
   - Crear dashboard para usuarios no-admin
   - Filtros avanzados
   - Exportación de observaciones

2. **Notificaciones Automáticas**
   - Alertar cuando hay observaciones críticas
   - Resumen diario por email
   - Integración con sistema de notificaciones

3. **Resolución Masiva**
   - Herramientas para resolver múltiples observaciones
   - Plantillas de resolución
   - Acciones automáticas

4. **Métricas y Reportes**
   - Dashboard de calidad de datos
   - Tendencias de observaciones
   - Identificación de problemas recurrentes

---

## 📚 Documentación Adicional

- Ver `apps/catalogo/models.py` para detalles del modelo
- Ver `apps/catalogo/utils.py` para lógica de importación
- Ver `apps/bienes/utils.py` para importación de bienes
- Ver `apps/catalogo/admin.py` para configuración del admin

---

## ✨ Resumen de Archivos Modificados

1. **Modelos:**
   - `apps/catalogo/models.py` - Nuevo modelo ImportObservation

2. **Utils:**
   - `apps/catalogo/utils.py` - Actualizado CatalogoImporter
   - `apps/bienes/utils.py` - Actualizado BienPatrimonialImporter

3. **Admin:**
   - `apps/catalogo/admin.py` - Nuevo admin para ImportObservation

4. **Templates:**
   - `templates/catalogo/importar.html` - Indicador de carga
   - `templates/bienes/importar.html` - Indicador de carga

5. **Migraciones:**
   - `apps/catalogo/migrations/0003_importobservation.py` - Nueva migración

---

**Fecha de Implementación:** 2025-01-09  
**Versión:** 1.0  
**Estado:** ✅ Completado y Listo para Producción
