# Requirements Document - Sistema de Papelera de Reciclaje

## Introduction

Este documento define los requerimientos para implementar un sistema de soft delete con papelera de reciclaje que permita la eliminación segura y recuperación de registros en todos los módulos del sistema de patrimonio. El sistema debe proporcionar una capa de seguridad adicional antes del borrado permanente, con controles de acceso estrictos.

## Requirements

### Requirement 1 - Soft Delete Universal

**User Story:** Como administrador del sistema, quiero que cuando se elimine cualquier registro (oficinas, bienes, catálogo), este se marque como eliminado sin borrarse físicamente de la base de datos, para poder recuperarlo si es necesario.

#### Acceptance Criteria

1. WHEN un usuario elimina un registro THEN el sistema SHALL marcar el registro como eliminado (deleted_at timestamp) sin borrarlo físicamente
2. WHEN se consultan registros normalmente THEN el sistema SHALL excluir automáticamente los registros marcados como eliminados
3. WHEN se marca un registro como eliminado THEN el sistema SHALL registrar quién lo eliminó y cuándo
4. IF un registro tiene relaciones dependientes THEN el sistema SHALL manejar el soft delete en cascada según las reglas de negocio
5. WHEN se elimina un registro THEN el sistema SHALL enviar una notificación al usuario confirmando la eliminación

### Requirement 2 - Papelera de Reciclaje Centralizada

**User Story:** Como administrador, quiero acceder a una papelera de reciclaje centralizada donde pueda ver todos los registros eliminados de todos los módulos, para gestionar las recuperaciones de manera eficiente.

#### Acceptance Criteria

1. WHEN accedo a la papelera de reciclaje THEN el sistema SHALL mostrar todos los registros eliminados de todos los módulos
2. WHEN visualizo la papelera THEN el sistema SHALL mostrar el tipo de registro, fecha de eliminación, usuario que eliminó, y tiempo restante antes del borrado permanente
3. WHEN filtro en la papelera THEN el sistema SHALL permitir filtrar por módulo, fecha de eliminación, usuario, y tipo de registro
4. WHEN busco en la papelera THEN el sistema SHALL permitir búsqueda por texto en los campos principales del registro
5. IF soy administrador THEN el sistema SHALL mostrar todos los registros eliminados
6. IF soy usuario regular THEN el sistema SHALL mostrar solo los registros que yo eliminé

### Requirement 3 - Recuperación de Registros

**User Story:** Como usuario autorizado, quiero poder restaurar registros desde la papelera de reciclaje, para recuperar información eliminada por error.

#### Acceptance Criteria

1. WHEN selecciono un registro en la papelera THEN el sistema SHALL permitir restaurarlo si tengo permisos
2. WHEN restauro un registro THEN el sistema SHALL remover la marca de eliminación y restaurar todas las relaciones dependientes
3. WHEN restauro un registro THEN el sistema SHALL registrar quién lo restauró y cuándo
4. WHEN restauro un registro THEN el sistema SHALL validar que no existan conflictos (ej: códigos duplicados)
5. IF existen conflictos al restaurar THEN el sistema SHALL mostrar opciones para resolverlos
6. WHEN se restaura exitosamente THEN el sistema SHALL enviar notificación de confirmación

### Requirement 4 - Eliminación Permanente con Código de Seguridad

**User Story:** Como administrador del sistema, quiero poder eliminar permanentemente registros de la papelera usando un código de seguridad especial, para liberar espacio y cumplir con políticas de retención de datos.

#### Acceptance Criteria

1. WHEN intento eliminar permanentemente un registro THEN el sistema SHALL solicitar un código de seguridad especial
2. WHEN ingreso el código de seguridad THEN el sistema SHALL validarlo contra una variable de entorno (PERMANENT_DELETE_CODE)
3. IF el código es correcto THEN el sistema SHALL proceder con la eliminación permanente
4. IF el código es incorrecto THEN el sistema SHALL denegar la operación y registrar el intento
5. WHEN se elimina permanentemente THEN el sistema SHALL registrar la acción en logs de auditoría
6. WHEN se elimina permanentemente THEN el sistema SHALL eliminar físicamente el registro y todas sus relaciones

### Requirement 5 - Eliminación Automática por Tiempo

**User Story:** Como administrador del sistema, quiero que los registros en la papelera se eliminen automáticamente después de un período configurable, para mantener el sistema limpio sin intervención manual constante.

#### Acceptance Criteria

1. WHEN un registro lleva más de X días en la papelera THEN el sistema SHALL eliminarlo permanentemente de forma automática
2. WHEN se configure el tiempo de retención THEN el sistema SHALL permitir diferentes períodos por tipo de registro
3. WHEN falten 7 días para la eliminación automática THEN el sistema SHALL enviar notificación de advertencia
4. WHEN falte 1 día para la eliminación automática THEN el sistema SHALL enviar notificación final
5. WHEN se ejecute la eliminación automática THEN el sistema SHALL generar un reporte de los registros eliminados

### Requirement 6 - Auditoría y Trazabilidad

**User Story:** Como auditor del sistema, quiero tener un registro completo de todas las operaciones de eliminación y recuperación, para mantener la trazabilidad de los cambios en el sistema.

#### Acceptance Criteria

1. WHEN se elimina un registro THEN el sistema SHALL registrar: usuario, fecha/hora, IP, motivo (si se proporciona)
2. WHEN se restaura un registro THEN el sistema SHALL registrar: usuario, fecha/hora, IP, estado anterior
3. WHEN se elimina permanentemente THEN el sistema SHALL registrar: usuario, fecha/hora, IP, código usado, datos del registro eliminado
4. WHEN consulto logs de auditoría THEN el sistema SHALL mostrar historial completo de operaciones de eliminación
5. WHEN genero reportes de auditoría THEN el sistema SHALL incluir estadísticas de eliminaciones y recuperaciones

### Requirement 7 - Interfaz de Usuario Intuitiva

**User Story:** Como usuario del sistema, quiero una interfaz clara y fácil de usar para gestionar la papelera de reciclaje, para poder realizar operaciones de recuperación de manera eficiente.

#### Acceptance Criteria

1. WHEN accedo a la papelera THEN el sistema SHALL mostrar una interfaz clara con iconografía intuitiva
2. WHEN veo un registro eliminado THEN el sistema SHALL mostrar vista previa de los datos principales
3. WHEN selecciono múltiples registros THEN el sistema SHALL permitir operaciones en lote (restaurar, eliminar permanentemente)
4. WHEN realizo una operación THEN el sistema SHALL mostrar confirmaciones claras y progress indicators
5. WHEN hay errores THEN el sistema SHALL mostrar mensajes descriptivos con acciones sugeridas

### Requirement 8 - Permisos y Seguridad

**User Story:** Como administrador de seguridad, quiero controlar qué usuarios pueden acceder a la papelera y qué operaciones pueden realizar, para mantener la seguridad de los datos.

#### Acceptance Criteria

1. WHEN un usuario intenta acceder a la papelera THEN el sistema SHALL verificar permisos específicos
2. WHEN un usuario ve la papelera THEN el sistema SHALL mostrar solo registros que tiene derecho a ver
3. WHEN un usuario intenta restaurar THEN el sistema SHALL verificar permisos de escritura en el módulo correspondiente
4. WHEN un usuario intenta eliminar permanentemente THEN el sistema SHALL verificar permisos de administrador
5. IF un usuario no tiene permisos THEN el sistema SHALL mostrar mensaje claro y registrar el intento

### Requirement 9 - Integración con Módulos Existentes

**User Story:** Como desarrollador, quiero que el sistema de papelera se integre transparentemente con todos los módulos existentes, para mantener la consistencia en toda la aplicación.

#### Acceptance Criteria

1. WHEN se implementa en un módulo THEN el sistema SHALL mantener la funcionalidad existente sin cambios
2. WHEN se elimina desde cualquier vista THEN el sistema SHALL usar automáticamente el soft delete
3. WHEN se listan registros THEN el sistema SHALL excluir automáticamente los eliminados
4. WHEN se exportan datos THEN el sistema SHALL excluir registros eliminados por defecto
5. WHEN se generan reportes THEN el sistema SHALL permitir incluir/excluir registros eliminados según configuración

### Requirement 10 - Configuración y Personalización

**User Story:** Como administrador del sistema, quiero poder configurar el comportamiento de la papelera según las necesidades de la organización, para adaptar el sistema a nuestras políticas internas.

#### Acceptance Criteria

1. WHEN configuro la papelera THEN el sistema SHALL permitir establecer diferentes períodos de retención por módulo
2. WHEN configuro notificaciones THEN el sistema SHALL permitir personalizar cuándo y cómo se envían
3. WHEN configuro permisos THEN el sistema SHALL permitir roles granulares para diferentes operaciones
4. WHEN configuro el código de seguridad THEN el sistema SHALL permitir cambiarlo desde variables de entorno
5. WHEN configuro la eliminación automática THEN el sistema SHALL permitir habilitarla/deshabilitarla por módulo