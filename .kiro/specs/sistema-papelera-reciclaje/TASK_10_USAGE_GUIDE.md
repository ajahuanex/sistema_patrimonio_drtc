# Guía de Uso - Vistas de Papelera de Reciclaje

## Acceso a la Papelera

### URL Principal
```
http://localhost:8000/core/papelera/
```

### Requisitos
- Usuario autenticado
- Permisos según rol:
  - **Usuarios regulares**: Ven solo sus propias eliminaciones
  - **Administradores**: Ven todas las eliminaciones

## Funcionalidades Principales

### 1. Vista de Lista (RecycleBinListView)

#### Estadísticas
Al entrar a la papelera, verás 4 tarjetas con estadísticas:
- **Total en Papelera**: Cantidad total de elementos eliminados
- **Próximos a Eliminar**: Elementos con 7 días o menos
- **Listos para Eliminar**: Elementos que ya cumplieron el tiempo de retención
- **Por Módulo**: Cantidad de módulos con elementos eliminados

#### Filtros Disponibles
1. **Búsqueda por texto**: Busca en nombre del objeto y motivo de eliminación
2. **Módulo**: Filtra por oficinas, bienes, catálogo o sistema
3. **Rango de fechas**: Desde/hasta fecha de eliminación
4. **Eliminado por**: Filtra por usuario (solo administradores)

#### Ejemplo de Uso de Filtros
```
# Buscar oficinas eliminadas en enero 2025
- Módulo: Oficinas
- Desde: 2025-01-01
- Hasta: 2025-01-31
- Click en botón de búsqueda
```

#### Tabla de Resultados
Cada fila muestra:
- Checkbox para selección
- Nombre del objeto
- Módulo (badge de color)
- Usuario que eliminó
- Fecha de eliminación
- Días restantes (con código de colores)
- Estado (badge indicador)
- Botones de acción

#### Códigos de Color
- 🔵 **Azul**: Más de 7 días restantes
- 🟡 **Amarillo**: 7 días o menos (advertencia)
- 🔴 **Rojo**: 0 días (listo para eliminar)

### 2. Vista de Detalle (RecycleBinDetailView)

#### Acceso
Click en el botón "ojo" (👁️) en cualquier elemento de la lista.

#### Información Mostrada

**Panel Izquierdo - Información General:**
- Nombre del objeto
- Módulo
- Tipo de modelo
- ID del objeto
- Estado actual

**Panel Derecho - Información de Eliminación:**
- Usuario que eliminó
- Fecha y hora de eliminación
- Fecha de eliminación automática
- Días restantes
- Motivo de eliminación

**Vista Previa de Datos:**
Tabla con todos los campos del objeto y sus valores originales.

#### Alertas
- **Conflicto de Restauración**: Si hay campos únicos duplicados
- **Objeto No Disponible**: Si el objeto ya no existe en BD

### 3. Restauración Individual

#### Desde la Lista
1. Click en botón verde "↩️" (Restaurar)
2. Confirmar en el diálogo
3. El objeto se restaura y redirige a su detalle

#### Desde el Detalle
1. Click en botón "Restaurar Elemento"
2. Confirmar en el diálogo
3. Redirección automática al objeto restaurado

#### Validaciones
- ✅ Permisos del usuario
- ✅ Conflictos de campos únicos
- ✅ Existencia del objeto
- ✅ Estado no restaurado previamente

### 4. Restauración en Lote (Bulk Restore)

#### Pasos
1. Seleccionar múltiples elementos con checkboxes
2. Click en "Restaurar Seleccionados" (botón verde)
3. Confirmar la operación
4. Ver resumen de resultados

#### Características
- Procesa cada elemento individualmente
- Muestra contador de éxitos y errores
- Lista errores específicos (máximo 5 en pantalla)
- No detiene el proceso si un elemento falla

#### Ejemplo de Mensaje
```
✅ Se restauraron 8 elemento(s) correctamente
❌ No se pudieron restaurar 2 elemento(s): 
   - Oficina Central: Ya existe un registro activo con código: CENTRAL
   - Bien 12345: Sin permisos
```

### 5. Eliminación Permanente (Solo Administradores)

#### Individual
1. Abrir detalle del elemento
2. Click en "Eliminar Permanentemente" (botón rojo)
3. Ingresar código de seguridad en el modal
4. Confirmar

#### En Lote
1. Seleccionar elementos con checkboxes
2. Click en "Eliminar Permanentemente" (botón rojo)
3. Ingresar código de seguridad en el modal
4. Confirmar

#### Código de Seguridad
El código debe estar configurado en las variables de entorno:
```python
# En settings.py o .env
PERMANENT_DELETE_CODE = 'tu-codigo-seguro-aqui'
```

#### Advertencias
- ⚠️ **Esta acción es IRREVERSIBLE**
- ⚠️ Los datos se eliminan físicamente de la base de datos
- ⚠️ Se registra en logs de auditoría
- ⚠️ Intentos fallidos se registran

## Casos de Uso Comunes

### Caso 1: Recuperar Oficina Eliminada por Error
```
1. Ir a /core/papelera/
2. Filtrar por módulo "Oficinas"
3. Buscar la oficina por nombre
4. Click en "Ver detalle"
5. Verificar que es la correcta
6. Click en "Restaurar Elemento"
7. Confirmar
```

### Caso 2: Limpiar Elementos Antiguos
```
1. Ir a /core/papelera/
2. Filtrar por fecha (ej: más de 90 días)
3. Seleccionar todos con checkbox principal
4. Click en "Eliminar Permanentemente"
5. Ingresar código de seguridad
6. Confirmar
```

### Caso 3: Revisar Eliminaciones de un Usuario
```
1. Ir a /core/papelera/ (como administrador)
2. Filtrar por "Eliminado por": nombre_usuario
3. Revisar lista de elementos
4. Restaurar si es necesario
```

### Caso 4: Restaurar Múltiples Bienes
```
1. Ir a /core/papelera/
2. Filtrar por módulo "Bienes Patrimoniales"
3. Seleccionar los bienes a restaurar
4. Click en "Restaurar Seleccionados"
5. Confirmar
6. Revisar resumen de resultados
```

## Permisos por Rol

### Usuario Regular (Funcionario)
- ✅ Ver papelera (solo sus eliminaciones)
- ✅ Ver detalle de sus elementos
- ✅ Restaurar sus propios elementos
- ❌ Ver elementos de otros usuarios
- ❌ Restaurar elementos de otros
- ❌ Eliminar permanentemente

### Administrador
- ✅ Ver papelera (todas las eliminaciones)
- ✅ Ver detalle de cualquier elemento
- ✅ Restaurar cualquier elemento
- ✅ Filtrar por usuario
- ✅ Eliminar permanentemente
- ✅ Operaciones en lote sin restricciones

### Auditor
- ✅ Ver papelera (todas las eliminaciones)
- ✅ Ver detalle de cualquier elemento
- ❌ Restaurar elementos
- ❌ Eliminar permanentemente

## Mensajes del Sistema

### Mensajes de Éxito
- ✅ "Objeto restaurado correctamente"
- ✅ "Se restauraron X elemento(s) correctamente"
- ✅ "Objeto eliminado permanentemente"

### Mensajes de Error
- ❌ "No tiene permisos para restaurar este elemento"
- ❌ "El objeto ya ha sido restaurado"
- ❌ "Conflicto al restaurar: Ya existe un registro activo con..."
- ❌ "Código de seguridad incorrecto"
- ❌ "Solo administradores pueden eliminar permanentemente"

### Mensajes de Advertencia
- ⚠️ "No se seleccionaron elementos"
- ⚠️ "El objeto ya no existe en la base de datos"

## Navegación

### Breadcrumbs
```
Papelera > Detalle
```

### Redirecciones Automáticas
Después de restaurar, el sistema intenta redirigir a:
- **Oficinas**: `/oficinas/<id>/`
- **Bienes**: `/bienes/<id>/`
- **Catálogo**: `/catalogo/<id>/`
- **Por defecto**: Lista de papelera

## Paginación

- 20 elementos por página
- Controles: Primera | Anterior | Página X de Y | Siguiente | Última
- Los filtros se mantienen al cambiar de página

## JavaScript Interactivo

### Selección de Checkboxes
- Click en checkbox principal: Selecciona/deselecciona todos
- Click en checkbox individual: Selecciona/deselecciona uno
- Contador dinámico: "X elemento(s) seleccionado(s)"
- Botones se habilitan/deshabilitan según selección

### Modales
- Confirmación de eliminación permanente
- Entrada de código de seguridad
- Validación en tiempo real

## Integración con Otros Módulos

### Oficinas
```python
# Eliminar oficina (automáticamente va a papelera)
oficina.delete()  # Usa soft_delete por defecto

# O explícitamente
RecycleBinService.soft_delete_object(oficina, user, "Motivo")
```

### Bienes Patrimoniales
```python
# Eliminar bien
bien.delete()  # Soft delete automático

# Restaurar desde papelera
entry = RecycleBin.objects.get(object_id=bien.id)
RecycleBinService.restore_object(entry, user)
```

### Catálogo
```python
# Eliminar categoría
categoria.delete()  # Soft delete

# Verificar en papelera
RecycleBin.objects.filter(module_name='catalogo')
```

## Troubleshooting

### Problema: No veo elementos en la papelera
**Solución**: 
- Verificar que hay elementos eliminados
- Verificar filtros aplicados
- Como usuario regular, solo ves tus eliminaciones

### Problema: No puedo restaurar un elemento
**Solución**:
- Verificar permisos
- Verificar conflictos de campos únicos
- Verificar que el objeto no esté ya restaurado

### Problema: Código de seguridad no funciona
**Solución**:
- Verificar configuración en settings.py
- Verificar variable de entorno PERMANENT_DELETE_CODE
- Verificar que eres administrador

### Problema: Error al restaurar en lote
**Solución**:
- Revisar mensajes de error específicos
- Restaurar elementos problemáticos individualmente
- Verificar conflictos de datos

## Mejores Prácticas

1. **Revisar antes de eliminar permanentemente**
   - Siempre verificar el detalle del elemento
   - Confirmar que no se necesitará en el futuro

2. **Usar motivos descriptivos**
   - Facilita búsquedas posteriores
   - Ayuda en auditorías

3. **Restaurar pronto**
   - No esperar hasta el último día
   - Evitar eliminación automática accidental

4. **Filtrar antes de operaciones en lote**
   - Asegurar que solo se seleccionan elementos correctos
   - Usar vista previa antes de confirmar

5. **Mantener código de seguridad seguro**
   - No compartir el código
   - Cambiar periódicamente
   - Usar código fuerte

## Soporte

Para más información:
- Ver documentación técnica: TASK_10_SUMMARY.md
- Ver verificación: TASK_10_VERIFICATION.md
- Revisar tests: tests/test_recycle_bin_views.py
