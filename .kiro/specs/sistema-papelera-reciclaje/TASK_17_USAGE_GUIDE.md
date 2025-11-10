# Task 17: Dashboard de Papelera - Guía de Uso Completa

## 📖 Introducción

El Dashboard de Estadísticas de Papelera proporciona una vista completa y visual del uso del sistema de papelera de reciclaje. Permite analizar tendencias, identificar patrones y exportar reportes para auditoría.

## 👥 Roles y Permisos

### Administrador
- **Acceso:** Completo a todas las estadísticas
- **Visualización:** Todos los elementos eliminados del sistema
- **Estadísticas:** Por módulo, usuario y tiempo
- **Exportación:** Todos los datos del sistema

### Usuario Regular (Funcionario)
- **Acceso:** Limitado a sus propios datos
- **Visualización:** Solo elementos que él eliminó
- **Estadísticas:** Por módulo y tiempo (solo sus datos)
- **Exportación:** Solo sus propios datos

## 🚀 Acceso al Dashboard

### Desde la Lista de Papelera

1. Navegar a **Papelera de Reciclaje**
2. En el header, clic en el botón **"Dashboard"** (icono de gráfico)
3. Se abre el dashboard con estadísticas

### Desde URL Directa

```
http://tu-dominio.com/core/papelera/dashboard/
```

### Desde Código

```python
from django.urls import reverse
from django.shortcuts import redirect

# Redirigir al dashboard
return redirect('core:recycle_bin_dashboard')
```

## 📊 Secciones del Dashboard

### 1. Filtro de Período

**Ubicación:** Parte superior del dashboard

**Opciones:**
- Últimos 7 días
- Últimos 30 días (predeterminado)
- Últimos 90 días
- Último año
- Todo el tiempo

**Uso:**
1. Seleccionar período del menú desplegable
2. El formulario se envía automáticamente
3. Todas las estadísticas se actualizan

**Ejemplo:**
```html
<!-- El filtro actualiza automáticamente -->
<select name="date_range" onchange="this.form.submit()">
    <option value="7">Últimos 7 días</option>
    <option value="30" selected>Últimos 30 días</option>
    <option value="90">Últimos 90 días</option>
</select>
```

### 2. Tarjetas de Estadísticas Generales

**Ubicación:** Fila superior con 4 tarjetas

#### Tarjeta 1: Total Eliminados
- **Color:** Púrpura
- **Muestra:** Número total de elementos eliminados en el período
- **Información adicional:** "En el período seleccionado"

#### Tarjeta 2: Restaurados
- **Color:** Verde-azul (éxito)
- **Muestra:** Número de elementos restaurados
- **Información adicional:** Tasa de restauración en porcentaje

#### Tarjeta 3: Pendientes
- **Color:** Azul (info)
- **Muestra:** Número de elementos aún en papelera
- **Información adicional:** "En papelera actualmente"

#### Tarjeta 4: Eliminados Permanentemente
- **Color:** Rosa-rojo (advertencia)
- **Muestra:** Número de elementos borrados definitivamente
- **Información adicional:** Tasa de eliminación permanente

**Interpretación:**
```
Total Eliminados = Restaurados + Pendientes + Eliminados Permanentemente
Tasa de Restauración = (Restaurados / Total) × 100%
```

### 3. Alertas de Elementos Próximos a Expirar

**Ubicación:** Debajo de las tarjetas de estadísticas

**Muestra cuando:**
- Hay elementos listos para eliminación automática
- Hay elementos cerca de eliminación automática (< 7 días)

**Ejemplo de Alerta:**
```
⚠️ Atención: 5 elemento(s) listo(s) para eliminación automática.
3 elemento(s) cerca de eliminación automática.
[Ver elementos]
```

**Acción:**
- Clic en "Ver elementos" redirige a la lista filtrada

### 4. Gráficos Interactivos

#### Gráfico 1: Elementos por Módulo

**Tipo:** Barras agrupadas
**Ubicación:** Superior izquierda
**Dimensiones:** 50% ancho, 300px alto

**Datos Mostrados:**
- Total eliminados (barra púrpura)
- Restaurados (barra verde)
- Pendientes (barra rosa)

**Módulos:**
- Oficinas
- Bienes Patrimoniales
- Catálogo
- Sistema

**Interacción:**
- Hover sobre barras muestra valor exacto
- Clic en leyenda oculta/muestra dataset
- Responsive: se adapta al tamaño de pantalla

**Interpretación:**
```
Ejemplo:
Oficinas: 10 eliminados, 3 restaurados, 7 pendientes
Bienes: 15 eliminados, 5 restaurados, 10 pendientes
```

#### Gráfico 2: Restauraciones vs Eliminaciones

**Tipo:** Dona (doughnut)
**Ubicación:** Superior derecha
**Dimensiones:** 50% ancho, 300px alto

**Datos Mostrados:**
- Restaurados (verde)
- Pendientes (azul)
- Eliminados Permanentemente (rosa)

**Interacción:**
- Hover muestra porcentaje y cantidad
- Clic en leyenda oculta/muestra segmento

**Interpretación:**
```
Ejemplo:
Restaurados: 30% (15 elementos)
Pendientes: 50% (25 elementos)
Permanentes: 20% (10 elementos)
```

#### Gráfico 3: Tendencia en el Tiempo

**Tipo:** Línea con área rellena
**Ubicación:** Centro, ancho completo
**Dimensiones:** 100% ancho, 250px alto

**Datos Mostrados:**
- Línea de eliminados (púrpura)
- Línea de restaurados (verde)
- Área rellena con transparencia

**Eje X:** Fechas (formato dd/mm/yyyy)
**Eje Y:** Cantidad de elementos

**Interacción:**
- Hover muestra fecha y valores exactos
- Zoom con scroll (si está habilitado)

**Interpretación:**
```
Ejemplo:
01/01/2025: 5 eliminados, 2 restaurados
02/01/2025: 3 eliminados, 1 restaurado
03/01/2025: 8 eliminados, 4 restaurados
```

**Análisis de Tendencias:**
- Picos indican días con alta actividad
- Líneas paralelas indican tasa de restauración constante
- Divergencia indica acumulación en papelera

#### Gráfico 4: Top 10 Usuarios (Solo Admin)

**Tipo:** Barras horizontales
**Ubicación:** Inferior, ancho completo
**Dimensiones:** 100% ancho, 300px alto

**Datos Mostrados:**
- Total eliminados (barra púrpura)
- Restaurados (barra verde)

**Usuarios:** Top 10 con más eliminaciones

**Interacción:**
- Hover muestra nombre completo y valores
- Ordenado de mayor a menor

**Interpretación:**
```
Ejemplo:
Juan Pérez: 25 eliminados, 10 restaurados
María García: 20 eliminados, 15 restaurados
```

### 5. Elementos Recientes

**Ubicación:** Dos columnas debajo de los gráficos

#### Eliminaciones Recientes (Izquierda)

**Muestra:** Últimos 5 elementos eliminados

**Información por Elemento:**
- Badge de módulo (color distintivo)
- Nombre del elemento (truncado a 50 caracteres)
- Usuario que eliminó
- Fecha y hora de eliminación
- Botón "Ver" para ir al detalle

**Ejemplo:**
```
[oficinas] Oficina Central
Por admin - 09/01/2025 10:30
[Ver]
```

#### Restauraciones Recientes (Derecha)

**Muestra:** Últimos 5 elementos restaurados

**Información por Elemento:**
- Badge de módulo
- Nombre del elemento
- Usuario que restauró
- Fecha y hora de restauración
- Badge "Restaurado" (verde)

**Ejemplo:**
```
[bienes] Computadora HP-001
Por admin - 08/01/2025 15:45
[Restaurado]
```

### 6. Tablas de Estadísticas Detalladas

#### Tabla 1: Estadísticas por Módulo

**Columnas:**
1. Módulo (con badge de color)
2. Total Eliminados
3. Restaurados
4. Pendientes
5. Tasa de Restauración (%)

**Ordenamiento:** Por total eliminados (descendente)

**Ejemplo:**
```
| Módulo    | Total | Restaurados | Pendientes | Tasa |
|-----------|-------|-------------|------------|------|
| Oficinas  | 25    | 10          | 15         | 40%  |
| Bienes    | 20    | 8           | 12         | 40%  |
| Catálogo  | 15    | 5           | 10         | 33%  |
```

#### Tabla 2: Estadísticas por Usuario (Solo Admin)

**Columnas:**
1. Usuario (nombre completo o username)
2. Total Eliminados
3. Restaurados
4. Pendientes
5. Tasa de Restauración (%)

**Ordenamiento:** Por total eliminados (descendente)
**Límite:** Top 10 usuarios

**Ejemplo:**
```
| Usuario      | Total | Restaurados | Pendientes | Tasa |
|--------------|-------|-------------|------------|------|
| Juan Pérez   | 30    | 15          | 15         | 50%  |
| María García | 25    | 10          | 15         | 40%  |
```

### 7. Exportación de Reportes

**Ubicación:** Parte inferior del dashboard

**Botones Disponibles:**

#### 1. Exportar CSV
- **Formato:** CSV con BOM UTF-8
- **Compatible:** Excel, Google Sheets
- **Incluye:** Todos los campos del registro
- **Nombre:** `reporte_papelera_YYYYMMDD_HHMMSS.csv`

#### 2. Exportar JSON
- **Formato:** JSON estructurado
- **Incluye:** Metadatos y datos
- **Uso:** Integración con otros sistemas
- **Nombre:** Respuesta JSON directa

#### 3. Exportar Solo Pendientes
- **Formato:** CSV
- **Filtro:** Solo elementos no restaurados
- **Uso:** Revisión de elementos en papelera

**Campos Exportados:**
```
- ID
- Módulo
- Tipo de Objeto
- Representación
- Eliminado Por
- Fecha de Eliminación
- Motivo
- Estado
- Restaurado Por
- Fecha de Restauración
- Eliminación Automática
```

## 📥 Guía de Exportación

### Exportar CSV Básico

**Pasos:**
1. Acceder al dashboard
2. Scroll hasta "Exportar Reportes"
3. Clic en "Exportar CSV"
4. El archivo se descarga automáticamente

**Resultado:**
```csv
ID,Módulo,Tipo de Objeto,Representación,...
1,oficinas,oficina,Oficina Central,...
2,bienes,bienpatrimonial,Computadora HP-001,...
```

### Exportar con Filtros

**Ejemplo 1: Solo Pendientes**
```
URL: /core/papelera/exportar/?format=csv&status=pending
```

**Ejemplo 2: Solo un Módulo**
```
URL: /core/papelera/exportar/?format=csv&module=oficinas
```

**Ejemplo 3: Período Específico**
```
URL: /core/papelera/exportar/?format=csv&date_range=7
```

**Ejemplo 4: Combinación**
```
URL: /core/papelera/exportar/?format=csv&date_range=30&status=pending&module=bienes
```

### Exportar JSON

**Pasos:**
1. Clic en "Exportar JSON"
2. Se descarga o muestra el JSON

**Estructura de Respuesta:**
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

## 🎯 Casos de Uso Prácticos

### Caso 1: Análisis Mensual de Eliminaciones

**Objetivo:** Revisar actividad del último mes

**Pasos:**
1. Acceder al dashboard
2. Seleccionar "Últimos 30 días"
3. Revisar tarjetas de estadísticas generales
4. Analizar gráfico de tendencia temporal
5. Identificar picos de actividad
6. Exportar CSV para reporte

**Análisis:**
- ¿Cuántos elementos se eliminaron?
- ¿Cuál es la tasa de restauración?
- ¿Hay días con actividad inusual?
- ¿Qué módulos tienen más eliminaciones?

### Caso 2: Auditoría de Usuario Específico

**Objetivo:** Revisar eliminaciones de un usuario (Admin)

**Pasos:**
1. Acceder al dashboard como administrador
2. Scroll hasta "Top 10 Usuarios"
3. Identificar usuario en el gráfico
4. Revisar tabla de estadísticas por usuario
5. Exportar datos filtrados si es necesario

**Análisis:**
- ¿Cuántos elementos eliminó el usuario?
- ¿Cuál es su tasa de restauración?
- ¿Es consistente con otros usuarios?

### Caso 3: Identificar Elementos en Riesgo

**Objetivo:** Encontrar elementos próximos a eliminación automática

**Pasos:**
1. Acceder al dashboard
2. Revisar alerta en la parte superior
3. Clic en "Ver elementos"
4. Se redirige a lista filtrada
5. Revisar elementos uno por uno
6. Restaurar si es necesario

**Análisis:**
- ¿Cuántos elementos están en riesgo?
- ¿Son elementos importantes?
- ¿Deben restaurarse o dejarse eliminar?

### Caso 4: Reporte para Dirección

**Objetivo:** Generar reporte ejecutivo

**Pasos:**
1. Acceder al dashboard
2. Seleccionar período (ej: último trimestre)
3. Capturar pantalla de gráficos
4. Exportar CSV con datos completos
5. Preparar presentación con:
   - Estadísticas generales
   - Gráficos de tendencias
   - Análisis por módulo
   - Recomendaciones

**Métricas Clave:**
- Total de eliminaciones
- Tasa de restauración
- Módulos más afectados
- Tendencias temporales

### Caso 5: Monitoreo Personal (Usuario Regular)

**Objetivo:** Revisar mis propias eliminaciones

**Pasos:**
1. Acceder al dashboard
2. Ver solo mis estadísticas
3. Revisar elementos recientes
4. Verificar elementos próximos a expirar
5. Restaurar si es necesario

**Análisis:**
- ¿Cuántos elementos he eliminado?
- ¿Cuántos he restaurado?
- ¿Hay elementos que debo recuperar?

## 🔍 Interpretación de Datos

### Tasas de Restauración

**Alta (> 50%):**
- Indica que muchos elementos se recuperan
- Posible uso de papelera como "archivo temporal"
- Considerar capacitación sobre eliminación

**Media (25-50%):**
- Uso normal del sistema
- Balance entre eliminaciones y restauraciones

**Baja (< 25%):**
- Pocas restauraciones
- Eliminaciones son definitivas
- Sistema usado correctamente

### Tendencias Temporales

**Picos Regulares:**
- Pueden indicar procesos periódicos
- Ej: limpieza mensual, cierre de período

**Picos Irregulares:**
- Eventos específicos
- Ej: reorganización, migración de datos

**Tendencia Creciente:**
- Aumento en uso del sistema
- Posible necesidad de más capacitación

**Tendencia Decreciente:**
- Reducción en eliminaciones
- Posible mejora en procesos

### Distribución por Módulo

**Desbalanceada:**
- Un módulo con muchas más eliminaciones
- Investigar causa
- Posible problema en ese módulo

**Balanceada:**
- Uso uniforme del sistema
- Indicador de salud del sistema

## 🛠️ Troubleshooting

### Problema: Dashboard no muestra datos

**Causas Posibles:**
1. No hay elementos en la papelera
2. Rango de fechas muy restrictivo
3. Usuario sin permisos

**Soluciones:**
1. Verificar que hay elementos eliminados
2. Cambiar a "Todo el tiempo"
3. Verificar rol del usuario

### Problema: Gráficos no se cargan

**Causas Posibles:**
1. Chart.js no cargó
2. Error en datos JSON
3. Bloqueador de scripts

**Soluciones:**
1. Verificar consola del navegador
2. Recargar página
3. Desactivar bloqueadores temporalmente

### Problema: Exportación falla

**Causas Posibles:**
1. No hay datos para exportar
2. Formato incorrecto
3. Permisos insuficientes

**Soluciones:**
1. Verificar filtros aplicados
2. Usar format=csv o format=json
3. Verificar autenticación

### Problema: CSV no abre en Excel

**Causas Posibles:**
1. Codificación incorrecta
2. Separadores no reconocidos

**Soluciones:**
1. El CSV incluye BOM UTF-8 automáticamente
2. Abrir con "Importar datos" en Excel
3. Usar Google Sheets como alternativa

## 📱 Uso en Dispositivos Móviles

### Adaptaciones Responsive

**Smartphone:**
- Tarjetas en columna única
- Gráficos adaptados al ancho
- Tablas con scroll horizontal
- Botones de tamaño táctil

**Tablet:**
- Tarjetas en 2 columnas
- Gráficos en 1-2 columnas
- Tablas completas

**Recomendaciones:**
- Usar en orientación vertical para tarjetas
- Rotar a horizontal para gráficos
- Exportar desde desktop para mejor experiencia

## 🎓 Mejores Prácticas

### Para Administradores

1. **Revisar dashboard semanalmente**
   - Identificar tendencias
   - Detectar anomalías
   - Planificar acciones

2. **Exportar reportes mensuales**
   - Mantener histórico
   - Análisis de tendencias
   - Auditoría

3. **Monitorear alertas**
   - Revisar elementos próximos a expirar
   - Contactar usuarios si es necesario
   - Ajustar políticas de retención

### Para Usuarios

1. **Revisar dashboard regularmente**
   - Verificar elementos propios
   - Restaurar si es necesario
   - Evitar pérdida de datos

2. **Usar filtros de fecha**
   - Enfocarse en período relevante
   - Reducir ruido visual
   - Análisis más preciso

3. **Exportar datos personales**
   - Mantener registro propio
   - Respaldo de información
   - Análisis personal

## 📚 Recursos Adicionales

### Documentación Relacionada
- [Guía de Papelera de Reciclaje](TASK_10_USAGE_GUIDE.md)
- [Sistema de Filtros](TASK_11_USAGE_GUIDE.md)
- [Eliminación Permanente](TASK_14_USAGE_EXAMPLES.md)

### Soporte
- Contactar al administrador del sistema
- Revisar logs de auditoría
- Consultar documentación técnica

### Capacitación
- Tutorial de uso del dashboard
- Interpretación de estadísticas
- Mejores prácticas de eliminación
