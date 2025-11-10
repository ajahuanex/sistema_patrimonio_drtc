# Guía de Uso - Sistema de Filtros Avanzados de Papelera

## Introducción

El sistema de filtros avanzados permite a los usuarios buscar y filtrar elementos en la papelera de reciclaje de manera eficiente y precisa. Esta guía explica cómo utilizar cada uno de los filtros disponibles.

## Acceso al Sistema

1. Navegar a la papelera de reciclaje: `/core/recycle-bin/`
2. Los filtros están disponibles en dos secciones:
   - **Filtros Rápidos**: Botones de acceso directo en la parte superior
   - **Filtros Avanzados**: Panel colapsable con todas las opciones

## Filtros Rápidos

### Listos para Eliminar
- **Descripción**: Muestra elementos cuya fecha de eliminación automática ya pasó
- **Uso**: Click en el botón "Listos para eliminar"
- **Badge**: Muestra el número de elementos en esta categoría
- **Color**: Rojo (urgente)

### Críticos (1-3 días)
- **Descripción**: Elementos que se eliminarán automáticamente en 1-3 días
- **Uso**: Click en el botón "Críticos (1-3 días)"
- **Color**: Rojo (alta prioridad)

### Advertencia (4-7 días)
- **Descripción**: Elementos que se eliminarán automáticamente en 4-7 días
- **Uso**: Click en el botón "Advertencia (4-7 días)"
- **Badge**: Muestra el número de elementos próximos a expirar
- **Color**: Amarillo (atención)

### Mis Eliminaciones
- **Descripción**: Muestra solo los elementos que el usuario actual eliminó
- **Uso**: Click en el botón "Mis eliminaciones"
- **Badge**: Muestra el número de elementos propios
- **Color**: Azul (información)

### Limpiar Filtros
- **Descripción**: Elimina todos los filtros aplicados
- **Uso**: Click en el botón "Limpiar filtros"
- **Resultado**: Vuelve a la vista por defecto (todos los elementos no restaurados)

## Filtros Avanzados

### Panel de Filtros

El panel de filtros avanzados se puede expandir/colapsar haciendo click en el encabezado "Filtros Avanzados". Se expande automáticamente cuando hay filtros activos.

### 1. Búsqueda por Texto

**Campo**: Buscar
**Tipo**: Texto libre
**Busca en**:
- Nombre del objeto eliminado
- Motivo de eliminación

**Ejemplo de uso**:
```
Buscar: "laptop"
Resultado: Encuentra "Laptop Dell Inspiron", "Laptop HP", etc.
```

### 2. Filtro por Módulo

**Campo**: Módulo
**Opciones**:
- Todos los módulos (por defecto)
- Oficinas
- Bienes Patrimoniales
- Catálogo
- Sistema

**Uso**: Seleccionar el módulo deseado del dropdown

**Ejemplo**:
```
Módulo: Bienes Patrimoniales
Resultado: Solo muestra bienes eliminados
```

### 3. Filtro por Tiempo Restante

**Campo**: Tiempo restante
**Opciones**:
- Cualquier tiempo (por defecto)
- Listos para eliminar (0 días)
- Crítico (1-3 días)
- Advertencia (4-7 días)
- Normal (8-14 días)
- Seguro (más de 14 días)

**Uso**: Seleccionar el rango de tiempo deseado

**Casos de uso**:
- **Listos para eliminar**: Para revisar elementos antes de eliminación automática
- **Crítico**: Para priorizar restauraciones urgentes
- **Advertencia**: Para planificar acciones en la semana
- **Normal**: Para revisión de mediano plazo
- **Seguro**: Para elementos con tiempo suficiente

### 4. Filtro por Estado

**Campo**: Estado
**Opciones**:
- Todos los estados (por defecto)
- En papelera
- Restaurados

**Uso**: Seleccionar el estado deseado

**Ejemplo**:
```
Estado: Restaurados
Resultado: Muestra historial de elementos restaurados
```

### 5. Filtro por Rango de Fechas

**Campos**: 
- Eliminado desde (fecha inicio)
- Eliminado hasta (fecha fin)

**Tipo**: Selector de fecha (calendario)

**Uso**: 
1. Seleccionar fecha de inicio (opcional)
2. Seleccionar fecha de fin (opcional)
3. Se puede usar solo una fecha o ambas

**Ejemplos**:
```
Desde: 01/01/2025, Hasta: 31/01/2025
Resultado: Elementos eliminados en enero 2025

Desde: 01/01/2025, Hasta: (vacío)
Resultado: Elementos eliminados desde enero 2025 hasta hoy

Desde: (vacío), Hasta: 31/01/2025
Resultado: Elementos eliminados hasta enero 2025
```

### 6. Filtro por Usuario (Solo Administradores)

**Campo**: Eliminado por
**Tipo**: Texto libre
**Busca en**:
- Nombre de usuario
- Nombre completo
- Apellido

**Disponibilidad**: Solo visible para usuarios con rol de administrador

**Ejemplo**:
```
Eliminado por: "juan"
Resultado: Encuentra elementos eliminados por "juan.perez", "Juan García", etc.
```

## Combinación de Filtros

Los filtros se pueden combinar para búsquedas más específicas. Todos los filtros activos se aplican con lógica AND (todos deben cumplirse).

### Ejemplo 1: Bienes críticos eliminados por usuario específico
```
Módulo: Bienes Patrimoniales
Tiempo restante: Crítico (1-3 días)
Eliminado por: admin
```

### Ejemplo 2: Oficinas eliminadas en diciembre con búsqueda
```
Módulo: Oficinas
Desde: 01/12/2024
Hasta: 31/12/2024
Buscar: "regional"
```

### Ejemplo 3: Elementos próximos a expirar de mis eliminaciones
```
Tiempo restante: Advertencia (4-7 días)
(Automáticamente filtra por usuario actual si no es admin)
```

## Resumen de Filtros Activos

Cuando hay filtros aplicados, se muestra un resumen visual en la parte inferior del panel de filtros:

```
Filtros activos: [Módulo: Oficinas] [Tiempo restante: Crítico (1-3 días)] [Búsqueda: laptop]
```

Cada filtro activo se muestra como un badge azul. Hay un botón "Limpiar" para eliminar todos los filtros.

## Aplicar Filtros

1. Seleccionar los filtros deseados
2. Click en el botón "Aplicar Filtros"
3. La página se recarga mostrando los resultados filtrados

## Paginación con Filtros

Cuando hay muchos resultados, se muestra paginación en la parte inferior. Los filtros se mantienen al cambiar de página:

- **Primera**: Va a la primera página manteniendo filtros
- **Anterior**: Página anterior con filtros
- **Siguiente**: Página siguiente con filtros
- **Última**: Última página con filtros

## Indicadores Visuales

### Badges de Tiempo Restante

Los elementos en la tabla muestran badges de colores según el tiempo restante:

- 🔴 **Rojo**: 0-3 días (urgente)
- 🟡 **Amarillo**: 4-7 días (advertencia)
- 🔵 **Azul**: 8-14 días (normal)
- 🟢 **Verde**: Más de 14 días (seguro)

### Badges de Estado

- 🔵 **Azul**: En papelera
- 🔴 **Rojo**: Listo para eliminar
- 🟡 **Amarillo**: Próximo a eliminar
- 🟢 **Verde**: Restaurado

### Contador de Filtros Activos

En el encabezado del panel de filtros avanzados se muestra un badge con el número de filtros activos:

```
Filtros Avanzados [3 activo(s)]
```

## Estadísticas

En la parte superior de la página se muestran 4 tarjetas con estadísticas:

1. **Total en Papelera**: Número total de elementos
2. **Próximos a Eliminar**: Elementos en los próximos 7 días
3. **Listos para Eliminar**: Elementos con fecha vencida
4. **Por Módulo**: Número de módulos con elementos

## Consejos de Uso

### Para Usuarios Regulares

1. **Revisar "Mis eliminaciones"** regularmente para no perder datos importantes
2. **Usar filtro de tiempo restante** para priorizar restauraciones
3. **Buscar por texto** cuando recuerdes parte del nombre del elemento

### Para Administradores

1. **Monitorear "Listos para eliminar"** diariamente
2. **Usar filtro por usuario** para auditar eliminaciones
3. **Combinar módulo + tiempo restante** para gestión eficiente
4. **Revisar elementos restaurados** para análisis de patrones

### Mejores Prácticas

1. **Limpiar filtros** antes de una nueva búsqueda para evitar confusión
2. **Usar filtros rápidos** para tareas comunes
3. **Guardar URLs** con filtros frecuentes como marcadores
4. **Revisar resumen de filtros activos** para confirmar criterios de búsqueda

## Solución de Problemas

### No aparecen resultados

1. Verificar que los filtros no sean demasiado restrictivos
2. Revisar el resumen de filtros activos
3. Limpiar filtros y buscar nuevamente
4. Verificar permisos (usuarios regulares solo ven sus eliminaciones)

### Los filtros no se aplican

1. Asegurarse de hacer click en "Aplicar Filtros"
2. Verificar que el formulario no tenga errores
3. Refrescar la página si es necesario

### Paginación pierde filtros

Si esto ocurre, es un bug. Los filtros deberían mantenerse automáticamente. Reportar al equipo de desarrollo.

## Ejemplos de Flujos de Trabajo

### Flujo 1: Restaurar elementos urgentes

1. Click en "Críticos (1-3 días)"
2. Revisar lista de elementos
3. Seleccionar elementos a restaurar
4. Click en "Restaurar Seleccionados"

### Flujo 2: Auditar eliminaciones de un usuario

1. Expandir "Filtros Avanzados"
2. Ingresar nombre de usuario en "Eliminado por"
3. Seleccionar rango de fechas
4. Click en "Aplicar Filtros"
5. Revisar resultados y exportar si es necesario

### Flujo 3: Limpiar papelera de elementos antiguos

1. Seleccionar "Tiempo restante: Seguro (más de 14 días)"
2. Revisar elementos que ya no son necesarios
3. Seleccionar elementos para eliminación permanente
4. Usar código de seguridad para eliminar

## Soporte

Para preguntas o problemas con el sistema de filtros:
- Consultar documentación técnica en `/docs`
- Contactar al administrador del sistema
- Reportar bugs al equipo de desarrollo
