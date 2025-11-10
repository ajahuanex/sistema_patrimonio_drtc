# Sistema de Observaciones de Importación

## 📋 Descripción General

Se ha implementado un sistema completo para registrar y gestionar observaciones durante la importación de datos en bloque. Este sistema permite continuar con las importaciones incluso cuando hay problemas menores, registrando todas las observaciones para revisión posterior.

## ✨ Características Principales

### 1. Modelo ImportObservation

**Ubicación:** `apps/catalogo/models.py`

Un modelo centralizado que registra todas las observaciones de importación de cualquier módulo del sistema.

**Campos Principales:**
- `modulo`: Módulo donde se generó (catálogo, bienes, oficinas)
- `tipo`: Tipo de observación (duplicado_denominacion, dato_incompleto, formato_invalido, referencia_faltante, otro)
- `severidad`: Nivel de severidad (info, warning, error)
- `fila_excel`: Número de fila en el archivo Excel
- `campo`: Campo que generó la observación
- `valor_original`: Valor original del campo
- `valor_procesado`: Valor después del procesamiento
- `mensaje`: Descripción detallada
- `datos_adicionales`: JSON con información adicional
- `resuelto`: Indica si fue revisada y resuelta
- `usuario`: Usuario que realizó la importación
- `archivo_nombre`: Nombre del archivo importado

### 2. Importación de Catálogo con Duplicados

**Cambios en:** `apps/catalogo/utils.py`

#### Comportamiento Anterior:
- Rechazaba registros con denominación duplicada
- Detenía la importación en caso de duplicados

#### Comportamiento Nuevo:
- **Permite duplicados en denominación** (configurable)
- Registra cada duplicado como observación
- Continúa con la importación
- Proporciona información detallada sobre los duplicados

**Parámetros Nuevos:**
```python
CatalogoImporter(
    usuario=None,                              # Usuario que importa
    archivo_nombre='',                         # Nombre del archivo
    permitir_duplicados_denominacion=True      # Permitir duplicados
)
```

**Ejemplo de Uso:**
```python
from apps/catalogo.utils import importar_catalogo_desde_excel

resultado = importar_catalogo_desde_excel(
    archivo_path='catalogo.xlsx',
    actualizar_existentes=False,
    usuario=request.user,
    archivo_nombre='catalogo_2025.xlsx',
    permitir_duplicados_denominacion=True  # Permitir duplicados
)

# Resultado incluye:
# - observaciones: Lista de observaciones registradas
# - total_observaciones: Cantidad de observaciones
```

### 3. Importación de Bienes con Validación Mejorada

**Cambios en:** `apps/bienes/utils.py`

#### Validaciones Agregadas:

1. **Múltiples Catálogos Encontrados:**
   - Detecta cuando hay múltiples catálogos con denominación similar
   - Registra observación con todos los catálogos encontrados
   - Usa el primero por defecto
   - Permite revisión posterior

2. **Coincidencia Parcial:**
   - Detecta cuando no hay coincidencia exacta
   - Busca coincidencia parcial (primera palabra)
   - Registra observación indicando el tipo de coincidencia
   - Permite validación posterior

3. **Catálogo No Encontrado:**
   - Registra observación con severidad "error"
   - Omite el registro pero continúa con la importación
   - Facilita corrección posterior

**Parámetros Nuevos:**
```python
BienPatrimonialImporter(
    usuario=None,
    archivo_nombre='',
    permitir_duplicados_denominacion=True
)
```

## 🎯 Casos de Uso

### Caso 1: Importar Catálogo con Duplicados

```python
# Vista de importación
def importar_catalogo(request):
    if request.method == 'POST':
        archivo = request.FILES['archivo']
        
        # Guardar archivo temporalmente
        temp_path = save_temp_file(archivo)
        
        # Importar permitiendo duplicados
        resultado = importar_catalogo_desde_excel(
            archivo_path=temp_path,
            actualizar_existentes=False,
            usuario=request.user,
            archivo_nombre=archivo.name,
            permitir_duplicados_denominacion=True
        )
        
        # Mostrar resultado
        if resultado['exito']:
            messages.success(request, f"Importación exitosa: {resultado['resumen']}")
            
            # Mostrar observaciones si las hay
            if resultado['total_observaciones'] > 0:
                messages.warning(
                    request,
                    f"Se registraron {resultado['total_observaciones']} observaciones. "
                    f"Revíselas en el panel de administración."
                )
        
        return redirect('catalogo:lista')
```

### Caso 2: Revisar Observaciones Pendientes

```python
from apps/catalogo.models import ImportObservation

# Obtener observaciones pendientes de catálogo
observaciones_catalogo = ImportObservation.obtener_pendientes(modulo='catalogo')

# Obtener observaciones de un archivo específico
observaciones_archivo = ImportObservation.obtener_por_archivo('catalogo_2025.xlsx')

# Marcar como resuelta
observacion.marcar_como_resuelto(
    usuario=request.user,
    notas='Se verificó que el duplicado es correcto'
)
```

### Caso 3: Importar Bienes con Validación

```python
def importar_bienes(request):
    if request.method == 'POST':
        archivo = request.FILES['archivo']
        temp_path = save_temp_file(archivo)
        
        resultado = importar_bienes_desde_excel(
            archivo_path=temp_path,
            actualizar_existentes=False,
            usuario=request.user,
            archivo_nombre=archivo.name,
            permitir_duplicados_denominacion=True
        )
        
        # Revisar observaciones
        for obs in resultado['observaciones']:
            if obs.tipo == 'duplicado_denominacion':
                # Notificar sobre duplicados
                print(f"Duplicado en fila {obs.fila_excel}: {obs.mensaje}")
```

## 🎨 Panel de Administración

### Visualización de Observaciones

El admin de Django incluye una interfaz completa para gestionar observaciones:

**Características:**
- Lista con badges de color por módulo, tipo y severidad
- Filtros por módulo, tipo, severidad, estado
- Búsqueda por mensaje, campo, archivo
- Jerarquía por fecha
- Acciones en lote (marcar como resuelto/pendiente)

**Acceso:**
```
/admin/catalogo/importobservation/
```

**Badges de Color:**
- 🔵 Módulo Catálogo (azul)
- 🟢 Módulo Bienes (verde)
- 🟣 Módulo Oficinas (morado)
- ⚠️ Warning (naranja)
- ❌ Error (rojo)
- ℹ️ Info (azul)

### Acciones Disponibles:

1. **Marcar como Resuelto:**
   - Seleccionar observaciones
   - Acción: "Marcar como resuelto"
   - Registra usuario y fecha de resolución

2. **Marcar como Pendiente:**
   - Revertir resolución
   - Limpiar datos de resolución

## 📊 Tipos de Observaciones

### 1. Duplicado de Denominación
**Tipo:** `duplicado_denominacion`
**Severidad:** `warning`
**Módulos:** Catálogo, Bienes

**Ejemplo:**
```
Fila 15: La denominación 'ESCRITORIO DE MADERA' ya existe en el catálogo 
con código(s): 04220001, 04220002
```

**Datos Adicionales:**
```json
{
    "codigo_nuevo": "04220003",
    "codigos_existentes": ["04220001", "04220002"],
    "permitido": true
}
```

### 2. Dato Incompleto
**Tipo:** `dato_incompleto`
**Severidad:** `warning`
**Módulos:** Todos

**Ejemplo:**
```
Fila 20: El campo 'Marca' está vacío
```

### 3. Formato Inválido
**Tipo:** `formato_invalido`
**Severidad:** `error`
**Módulos:** Todos

**Ejemplo:**
```
Fila 25: El código '123' no tiene el formato correcto (debe ser 8 dígitos)
```

### 4. Referencia Faltante
**Tipo:** `referencia_faltante`
**Severidad:** `error`
**Módulos:** Bienes, Oficinas

**Ejemplo:**
```
Fila 30: No se encontró catálogo para la denominación 'SILLA GIRATORIA'
```

**Datos Adicionales:**
```json
{
    "codigo_patrimonial": "PAT-2025-001",
    "denominacion_buscada": "SILLA GIRATORIA"
}
```

### 5. Otro
**Tipo:** `otro`
**Severidad:** `info`
**Módulos:** Todos

**Ejemplo:**
```
Fila 35: Se aplicó valor por defecto 'ACTIVO' al campo Estado
```

## 🔧 Configuración

### Permitir/Denegar Duplicados

**En Catálogo:**
```python
# Permitir duplicados (por defecto)
resultado = importar_catalogo_desde_excel(
    archivo_path=path,
    permitir_duplicados_denominacion=True
)

# Denegar duplicados (comportamiento estricto)
resultado = importar_catalogo_desde_excel(
    archivo_path=path,
    permitir_duplicados_denominacion=False
)
```

**En Bienes:**
```python
# Permitir múltiples coincidencias (por defecto)
resultado = importar_bienes_desde_excel(
    archivo_path=path,
    permitir_duplicados_denominacion=True
)
```

## 📈 Reportes y Estadísticas

### Consultas Útiles

```python
from apps.catalogo.models import ImportObservation
from django.db.models import Count

# Observaciones por módulo
stats_modulo = ImportObservation.objects.values('modulo').annotate(
    total=Count('id')
).order_by('-total')

# Observaciones por tipo
stats_tipo = ImportObservation.objects.values('tipo').annotate(
    total=Count('id')
).order_by('-total')

# Observaciones pendientes por severidad
pendientes = ImportObservation.objects.filter(resuelto=False).values(
    'severidad'
).annotate(total=Count('id'))

# Observaciones de un usuario específico
mis_observaciones = ImportObservation.objects.filter(
    usuario=request.user,
    resuelto=False
).order_by('-fecha_importacion')

# Observaciones de la última semana
from datetime import timedelta
from django.utils import timezone

ultima_semana = timezone.now() - timedelta(days=7)
recientes = ImportObservation.objects.filter(
    fecha_importacion__gte=ultima_semana
).order_by('-fecha_importacion')
```

## 🚀 Migración

### Aplicar Migración

```bash
# Crear migración (ya creada)
python manage.py makemigrations catalogo

# Aplicar migración
python manage.py migrate catalogo
```

### Migración Incluida

**Archivo:** `apps/catalogo/migrations/0003_importobservation.py`

Crea la tabla `catalogo_importobservation` con todos los campos e índices necesarios.

## ✅ Beneficios

1. **Continuidad de Importación:**
   - No se detiene por problemas menores
   - Registra todo para revisión posterior
   - Maximiza datos importados

2. **Trazabilidad Completa:**
   - Registro de cada observación
   - Usuario y fecha de importación
   - Archivo de origen

3. **Gestión Eficiente:**
   - Panel de administración intuitivo
   - Filtros y búsquedas avanzadas
   - Acciones en lote

4. **Flexibilidad:**
   - Configurable por importación
   - Diferentes niveles de severidad
   - Datos adicionales en JSON

5. **Auditoría:**
   - Historial completo
   - Estado de resolución
   - Notas de resolución

## 📝 Notas de Implementación

### Compatibilidad

- Compatible con importaciones existentes
- No rompe funcionalidad anterior
- Parámetros opcionales con valores por defecto

### Performance

- Índices optimizados para consultas frecuentes
- Transacciones atómicas
- Procesamiento eficiente

### Seguridad

- Solo administradores pueden eliminar observaciones
- No se pueden crear observaciones manualmente
- Registro de usuario en cada operación

## 🎯 Próximos Pasos

### Mejoras Futuras

1. **Vista Web de Observaciones:**
   - Interfaz para usuarios no admin
   - Dashboard de observaciones
   - Exportación de reportes

2. **Notificaciones:**
   - Email cuando hay observaciones críticas
   - Alertas en el sistema
   - Resumen semanal

3. **Resolución Automática:**
   - Reglas para auto-resolver observaciones
   - Sugerencias de corrección
   - Aprendizaje de patrones

4. **Integración con Workflow:**
   - Aprobación de importaciones con observaciones
   - Flujo de revisión
   - Validación por supervisor

## 📚 Documentación Relacionada

- `CATALOGO_PLANTILLA_IMPLEMENTACION.md` - Plantilla de importación de catálogo
- `BIENES_PLANTILLA_IMPLEMENTACION.md` - Plantilla de importación de bienes
- `PLANTILLAS_IMPORTACION_RESUMEN.md` - Resumen general de plantillas

## 🎉 Conclusión

El sistema de observaciones de importación proporciona una solución robusta y flexible para manejar problemas durante las importaciones en bloque. Permite continuar con las importaciones mientras mantiene un registro completo de todas las observaciones para revisión y corrección posterior.

**Características Clave:**
- ✅ Permite duplicados en denominación (configurable)
- ✅ Registra todas las observaciones
- ✅ Panel de administración completo
- ✅ Trazabilidad total
- ✅ Gestión eficiente
- ✅ Compatible con código existente
