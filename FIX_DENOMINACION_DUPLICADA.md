# Fix: Permitir Denominaciones Duplicadas en Catálogo

## Problema

El sistema estaba rechazando registros de catálogo con denominaciones duplicadas, mostrando el error:
```
Ya existe Catálogo con este Denominación del Bien.
```

## Solución Implementada

Se modificó el sistema para permitir denominaciones duplicadas y registrarlas como observaciones en lugar de errores.

### Cambios Realizados

#### 1. Modelo `Catalogo` (`apps/catalogo/models.py`)
- **Removido**: `unique=True` del campo `denominacion`
- **Razón**: Permitir que múltiples catálogos tengan la misma denominación

#### 2. Migración de Base de Datos
- **Creada**: `0004_remove_denominacion_unique.py`
- **Aplicada**: Exitosamente con `docker-compose exec web python manage.py migrate catalogo`
- **Efecto**: Eliminó la restricción UNIQUE de la columna `denominacion` en la tabla `catalogo_catalogo`

#### 3. Lógica de Importación (`apps/catalogo/utils.py`)
La lógica ya estaba implementada correctamente:
- Detecta denominaciones duplicadas
- Crea observaciones en la tabla `ImportObservation`
- Permite continuar con la importación si `permitir_duplicados_denominacion=True`
- Registra información detallada sobre los duplicados

#### 4. Vista de Importación (`apps/catalogo/views.py`)
- **Actualizado**: Llamada a `importar_catalogo_desde_excel()` para incluir:
  - `usuario=request.user`: Usuario que realiza la importación
  - `archivo_nombre=archivo.name`: Nombre del archivo Excel
  - `permitir_duplicados_denominacion=True`: Permitir duplicados
- **Agregado**: Mensaje informativo sobre observaciones registradas

## Comportamiento Actual

### Cuando se Importa un Catálogo con Denominación Duplicada:

1. **El registro SE CREA** exitosamente
2. **Se registra una observación** en la tabla `ImportObservation` con:
   - Tipo: `duplicado_denominacion`
   - Severidad: `warning`
   - Mensaje descriptivo indicando los códigos existentes
   - Datos adicionales en JSON

3. **Se muestra un mensaje** al usuario:
   - Advertencia: "Fila X: Denominación 'NOMBRE' duplicada, pero se permite continuar"
   - Info: "Se registraron N observaciones durante la importación"

### Ejemplo de Observación Registrada:

```python
ImportObservation.objects.create(
    modulo='catalogo',
    tipo='duplicado_denominacion',
    severidad='warning',
    fila_excel=260,
    campo='Denominación',
    mensaje="La denominación 'LAPTOP HP' ya existe en el catálogo con código(s): 04220001, 04220002",
    valor_original='LAPTOP HP',
    valor_procesado='LAPTOP HP',
    usuario=request.user,
    archivo_nombre='catalogo_2024.xlsx',
    datos_adicionales={
        'codigo_nuevo': '04220003',
        'codigos_existentes': ['04220001', '04220002'],
        'permitido': True
    }
)
```

## Verificación

### 1. Verificar que la Migración se Aplicó

```bash
docker-compose exec web python manage.py showmigrations catalogo
```

Deberías ver:
```
catalogo
 [X] 0001_initial
 [X] 0002_...
 [X] 0003_importobservation
 [X] 0004_remove_denominacion_unique
```

### 2. Verificar en la Base de Datos

```bash
docker-compose exec db psql -U postgres -d patrimonio_db
```

```sql
-- Verificar que no hay restricción UNIQUE en denominacion
\d catalogo_catalogo

-- Debería mostrar que denominacion NO tiene UNIQUE
```

### 3. Probar la Importación

1. Ir a: http://localhost:8000/catalogo/importar/
2. Subir un archivo Excel con denominaciones duplicadas
3. Verificar que:
   - Los registros se crean exitosamente
   - Se muestran advertencias sobre duplicados
   - Se muestra mensaje sobre observaciones registradas

### 4. Ver las Observaciones

```bash
docker-compose exec web python manage.py shell
```

```python
from apps.catalogo.models import ImportObservation

# Ver todas las observaciones
obs = ImportObservation.objects.all()
for o in obs:
    print(f"Fila {o.fila_excel}: {o.mensaje}")

# Ver solo duplicados de denominación
duplicados = ImportObservation.objects.filter(tipo='duplicado_denominacion')
print(f"Total duplicados: {duplicados.count()}")
```

## Ventajas de Esta Solución

1. **Flexibilidad**: Permite catálogos con la misma denominación pero diferentes códigos
2. **Trazabilidad**: Todas las denominaciones duplicadas quedan registradas
3. **No Bloquea**: La importación continúa sin interrupciones
4. **Auditable**: Se puede revisar el historial de observaciones
5. **Informativo**: El usuario es notificado sobre los duplicados

## Modelo de Datos

### Tabla `catalogo_catalogo`
```sql
codigo VARCHAR(20) UNIQUE NOT NULL
denominacion VARCHAR(500) NOT NULL  -- Ya NO tiene UNIQUE
grupo VARCHAR(50)
clase VARCHAR(50)
resolucion VARCHAR(100)
estado VARCHAR(20)
```

### Tabla `catalogo_importobservation`
```sql
id SERIAL PRIMARY KEY
modulo VARCHAR(50)
tipo VARCHAR(50)
severidad VARCHAR(20)
fila_excel INTEGER
campo VARCHAR(100)
valor_original TEXT
valor_procesado TEXT
mensaje TEXT
datos_adicionales JSONB
fecha_importacion TIMESTAMP
usuario_id INTEGER
archivo_nombre VARCHAR(255)
resuelto BOOLEAN DEFAULT FALSE
```

## Próximos Pasos (Opcional)

Si deseas agregar una interfaz para revisar las observaciones:

1. **Vista de Observaciones**: Crear una vista para listar y filtrar observaciones
2. **Dashboard**: Agregar widget en el dashboard mostrando observaciones pendientes
3. **Exportar**: Permitir exportar observaciones a Excel
4. **Resolver**: Agregar funcionalidad para marcar observaciones como resueltas

## Conclusión

El sistema ahora permite denominaciones duplicadas en el catálogo y las registra como observaciones para revisión posterior. Esto proporciona flexibilidad sin perder trazabilidad.
