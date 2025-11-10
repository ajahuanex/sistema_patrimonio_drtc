# Guía de Usuario - Sistema de Papelera de Reciclaje

## Introducción

El Sistema de Papelera de Reciclaje proporciona una capa de seguridad adicional antes de eliminar permanentemente registros del sistema de patrimonio. Cuando eliminas un registro (oficina, bien patrimonial o catálogo), este se mueve a la papelera donde puede ser recuperado antes de su eliminación definitiva.

## Características Principales

- **Eliminación Segura**: Los registros eliminados se marcan como eliminados pero no se borran físicamente
- **Recuperación Fácil**: Restaura registros eliminados por error con un solo clic
- **Eliminación Automática**: Los registros se eliminan permanentemente después de un período configurable
- **Notificaciones**: Recibe alertas antes de que los registros se eliminen permanentemente
- **Auditoría Completa**: Todas las operaciones quedan registradas para trazabilidad

## Acceso a la Papelera

### Desde el Menú Principal

1. Inicia sesión en el sistema
2. En el menú principal, haz clic en **"Papelera de Reciclaje"**
3. Verás un contador con el número de elementos en la papelera

### Desde Listados de Módulos

Cada módulo (Oficinas, Bienes, Catálogo) tiene un acceso rápido a la papelera:
- Busca el ícono de papelera en la parte superior del listado
- El contador muestra cuántos elementos de ese módulo están en la papelera

## Operaciones Básicas

### Ver Elementos en la Papelera

La vista principal de la papelera muestra:
- **Tipo de registro**: Oficina, Bien Patrimonial o Catálogo
- **Información del registro**: Nombre o código identificador
- **Fecha de eliminación**: Cuándo fue eliminado
- **Eliminado por**: Usuario que realizó la eliminación
- **Tiempo restante**: Días antes de la eliminación automática
- **Estado**: Indicador visual del tiempo restante

#### Códigos de Color

- 🟢 **Verde**: Más de 7 días restantes
- 🟡 **Amarillo**: Entre 3 y 7 días restantes
- 🟠 **Naranja**: Entre 1 y 3 días restantes
- 🔴 **Rojo**: Menos de 1 día restante

### Buscar y Filtrar

#### Búsqueda por Texto
Usa la barra de búsqueda para encontrar registros por:
- Nombre
- Código
- Descripción

#### Filtros Disponibles

1. **Por Módulo**
   - Todos los módulos
   - Solo Oficinas
   - Solo Bienes Patrimoniales
   - Solo Catálogos

2. **Por Fecha de Eliminación**
   - Última semana
   - Último mes
   - Últimos 3 meses
   - Rango personalizado

3. **Por Usuario**
   - Mis eliminaciones
   - Eliminaciones de otros usuarios (solo administradores)

4. **Por Tiempo Restante**
   - Próximos a eliminarse (< 3 días)
   - Tiempo medio (3-7 días)
   - Tiempo amplio (> 7 días)

### Restaurar Registros

#### Restauración Individual

1. Localiza el registro en la papelera
2. Haz clic en el botón **"Ver Detalles"**
3. Revisa la información del registro
4. Haz clic en **"Restaurar"**
5. Confirma la operación
6. El registro volverá a su estado original

#### Restauración Múltiple

1. Selecciona los registros usando las casillas de verificación
2. Haz clic en **"Restaurar Seleccionados"** en la parte superior
3. Confirma la operación
4. Todos los registros seleccionados serán restaurados

#### Validaciones de Restauración

El sistema valida automáticamente:
- **Conflictos de unicidad**: Si ya existe un registro con el mismo código
- **Dependencias**: Si las relaciones necesarias están disponibles
- **Permisos**: Si tienes autorización para restaurar

Si hay conflictos, el sistema te mostrará opciones para resolverlos:
- Asignar un nuevo código
- Fusionar con el registro existente
- Cancelar la operación

### Ver Detalles de un Registro

1. Haz clic en el nombre del registro o en **"Ver Detalles"**
2. Verás una vista previa con:
   - Información completa del registro
   - Historial de cambios
   - Relaciones con otros registros
   - Opciones de restauración o eliminación

## Notificaciones

### Notificaciones de Advertencia

Recibirás notificaciones automáticas:

#### Primera Advertencia (7 días antes)
- **Asunto**: "Elementos próximos a eliminarse de la papelera"
- **Contenido**: Lista de registros que se eliminarán en 7 días
- **Acción**: Revisa y restaura si es necesario

#### Advertencia Final (1 día antes)
- **Asunto**: "URGENTE: Elementos se eliminarán mañana"
- **Contenido**: Lista de registros que se eliminarán en 24 horas
- **Acción**: Última oportunidad para restaurar

### Configurar Notificaciones

1. Ve a **"Mi Perfil"** → **"Preferencias"**
2. En la sección **"Notificaciones de Papelera"**:
   - Activa/desactiva notificaciones por email
   - Configura notificaciones en el sistema
   - Establece frecuencia de resúmenes

## Eliminación Permanente

⚠️ **ADVERTENCIA**: La eliminación permanente es irreversible.

### Requisitos

- Debes ser **Administrador del Sistema**
- Necesitas el **Código de Seguridad** especial
- La operación queda registrada en auditoría

### Proceso

1. Selecciona el registro a eliminar permanentemente
2. Haz clic en **"Eliminar Permanentemente"**
3. Lee la advertencia cuidadosamente
4. Ingresa el **Código de Seguridad**
5. Confirma la operación
6. El registro se eliminará físicamente de la base de datos

### Protecciones de Seguridad

- **Límite de intentos**: 3 intentos fallidos bloquean temporalmente
- **CAPTCHA**: Se activa después de 2 intentos fallidos
- **Auditoría**: Todos los intentos quedan registrados
- **Notificación**: Los administradores reciben alertas de intentos fallidos

## Permisos y Roles

### Usuario Regular

- Ver elementos que yo eliminé
- Restaurar mis propios elementos
- Recibir notificaciones de mis elementos

### Funcionario

- Ver elementos de mi oficina
- Restaurar elementos de mi oficina
- Ver estadísticas de mi oficina

### Administrador

- Ver todos los elementos eliminados
- Restaurar cualquier elemento
- Eliminar permanentemente con código de seguridad
- Acceder a reportes de auditoría
- Configurar políticas de retención

### Auditor

- Ver todos los elementos eliminados (solo lectura)
- Acceder a reportes de auditoría completos
- Exportar logs de auditoría
- Ver estadísticas del sistema

## Dashboard de Estadísticas

### Acceso

1. Ve a **"Papelera de Reciclaje"**
2. Haz clic en **"Dashboard"** en el menú superior

### Métricas Disponibles

#### Resumen General
- Total de elementos en papelera
- Elementos por módulo
- Elementos próximos a eliminarse
- Espacio ocupado

#### Gráficos

1. **Eliminaciones por Módulo**
   - Gráfico de pastel mostrando distribución

2. **Tendencia de Eliminaciones**
   - Gráfico de líneas por período

3. **Restauraciones vs Eliminaciones**
   - Comparativa de operaciones

4. **Usuarios Más Activos**
   - Top 10 usuarios con más eliminaciones

#### Exportar Reportes

- **PDF**: Reporte completo con gráficos
- **Excel**: Datos detallados para análisis
- **CSV**: Datos en formato plano

## Mejores Prácticas

### Para Usuarios

1. **Revisa antes de eliminar**: Asegúrate de que realmente quieres eliminar
2. **Usa la papelera como temporal**: No la uses como almacenamiento permanente
3. **Revisa notificaciones**: Atiende las alertas de eliminación próxima
4. **Documenta razones**: Agrega motivos al eliminar para auditoría

### Para Administradores

1. **Configura retención apropiada**: Ajusta días según necesidades
2. **Monitorea el dashboard**: Revisa estadísticas regularmente
3. **Protege el código de seguridad**: Cámbialo periódicamente
4. **Revisa auditoría**: Verifica patrones sospechosos
5. **Capacita usuarios**: Asegura que entiendan el sistema

## Solución de Problemas

### No puedo restaurar un registro

**Posibles causas:**
- No tienes permisos suficientes
- Existe un conflicto de unicidad
- Las dependencias no están disponibles

**Solución:**
1. Verifica tus permisos con el administrador
2. Revisa los mensajes de error específicos
3. Contacta al administrador si persiste

### No recibo notificaciones

**Posibles causas:**
- Notificaciones desactivadas en preferencias
- Email incorrecto en tu perfil
- Filtros de spam

**Solución:**
1. Verifica configuración en **"Mi Perfil"**
2. Actualiza tu email si es necesario
3. Revisa carpeta de spam
4. Contacta al administrador del sistema

### El código de seguridad no funciona

**Posibles causas:**
- Código incorrecto
- Cuenta bloqueada temporalmente
- No tienes permisos de administrador

**Solución:**
1. Verifica que eres administrador
2. Espera 30 minutos si estás bloqueado
3. Contacta al administrador principal para el código correcto

### Un registro no aparece en la papelera

**Posibles causas:**
- Fue eliminado permanentemente
- No tienes permisos para verlo
- Filtros activos lo ocultan

**Solución:**
1. Limpia todos los filtros
2. Verifica con el administrador si fue eliminado permanentemente
3. Revisa los logs de auditoría

## Preguntas Frecuentes

### ¿Cuánto tiempo permanecen los registros en la papelera?

Por defecto, 30 días. Los administradores pueden configurar diferentes períodos por módulo.

### ¿Puedo recuperar un registro después de la eliminación permanente?

No. La eliminación permanente es irreversible. Solo se puede recuperar desde backups del sistema.

### ¿Qué pasa con las relaciones cuando elimino un registro?

Las relaciones se mantienen. Al restaurar, todas las relaciones se recuperan automáticamente.

### ¿Puedo ver quién eliminó un registro?

Sí, la información del usuario que eliminó aparece en los detalles del registro.

### ¿Los registros eliminados afectan los reportes?

No. Los registros eliminados se excluyen automáticamente de todos los reportes y estadísticas.

### ¿Puedo desactivar la eliminación automática?

Los administradores pueden desactivarla por módulo en la configuración del sistema.

## Contacto y Soporte

Para asistencia adicional:
- **Email**: soporte@patrimonio.gob
- **Teléfono**: +XXX-XXX-XXXX
- **Documentación técnica**: Ver RECYCLE_BIN_TECHNICAL_GUIDE.md
- **Reportar problemas**: Usa el sistema de tickets interno
