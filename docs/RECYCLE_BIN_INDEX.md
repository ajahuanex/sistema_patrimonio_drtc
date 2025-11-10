# Índice de Documentación - Sistema de Papelera de Reciclaje

## Bienvenido

Este es el índice completo de la documentación del Sistema de Papelera de Reciclaje. Encuentra rápidamente la información que necesitas según tu rol y necesidades.

## 📚 Documentación por Rol

### Para Usuarios Finales

- **[Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md)** - Cómo usar la papelera de reciclaje
  - Acceso a la papelera
  - Buscar y filtrar elementos
  - Restaurar registros
  - Entender notificaciones
  - Preguntas frecuentes

### Para Administradores

- **[Guía de Configuración](RECYCLE_BIN_CONFIGURATION.md)** - Configurar el sistema
  - Variables de entorno
  - Configuración por módulo
  - Permisos y roles
  - Notificaciones
  - Seguridad

- **[Comandos de Management](RECYCLE_BIN_COMMANDS.md)** - Administración por línea de comandos
  - cleanup_recycle_bin
  - setup_recycle_bin
  - generate_recycle_report
  - Y más...

### Para Desarrolladores

- **[Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md)** - Arquitectura y desarrollo
  - Arquitectura del sistema
  - Modelos de datos
  - APIs y servicios
  - Integración con módulos
  - Testing

- **[Guía de Inicio Rápido](RECYCLE_BIN_QUICK_START.md)** - Implementación rápida
  - Instalación en 5 pasos
  - Verificación
  - Uso básico
  - Troubleshooting

## 📖 Documentación por Tema

### Instalación y Configuración

1. [Inicio Rápido](RECYCLE_BIN_QUICK_START.md#instalación-en-5-pasos)
2. [Variables de Entorno](RECYCLE_BIN_CONFIGURATION.md#variables-de-entorno)
3. [Configuración de Base de Datos](RECYCLE_BIN_CONFIGURATION.md#configuración-de-base-de-datos)
4. [Configuración de Celery](RECYCLE_BIN_CONFIGURATION.md#configuración-de-celery-beat)

### Uso Diario

1. [Acceder a la Papelera](RECYCLE_BIN_USER_GUIDE.md#acceso-a-la-papelera)
2. [Buscar y Filtrar](RECYCLE_BIN_USER_GUIDE.md#buscar-y-filtrar)
3. [Restaurar Registros](RECYCLE_BIN_USER_GUIDE.md#restaurar-registros)
4. [Ver Estadísticas](RECYCLE_BIN_USER_GUIDE.md#dashboard-de-estadísticas)

### Administración

1. [Configurar Retención](RECYCLE_BIN_CONFIGURATION.md#configuración-por-módulo)
2. [Gestionar Permisos](RECYCLE_BIN_CONFIGURATION.md#configuración-de-roles-y-permisos)
3. [Limpieza Automática](RECYCLE_BIN_COMMANDS.md#cleanup_recycle_bin)
4. [Generar Reportes](RECYCLE_BIN_COMMANDS.md#generate_recycle_report)

### Desarrollo

1. [Arquitectura](RECYCLE_BIN_TECHNICAL_GUIDE.md#arquitectura-del-sistema)
2. [Modelos de Datos](RECYCLE_BIN_TECHNICAL_GUIDE.md#modelos-de-datos)
3. [Servicios](RECYCLE_BIN_TECHNICAL_GUIDE.md#servicios)
4. [APIs](RECYCLE_BIN_TECHNICAL_GUIDE.md#apis-y-endpoints)
5. [Testing](RECYCLE_BIN_TECHNICAL_GUIDE.md#testing)

### Seguridad

1. [Código de Seguridad](RECYCLE_BIN_CONFIGURATION.md#permanent_delete_code)
2. [Permisos](RECYCLE_BIN_CONFIGURATION.md#configuración-de-roles-y-permisos)
3. [Rate Limiting](RECYCLE_BIN_CONFIGURATION.md#rate-limiting)
4. [Auditoría](RECYCLE_BIN_TECHNICAL_GUIDE.md#deletionauditlog-model)

## 🚀 Guías de Inicio Rápido

### Nuevo Usuario
1. Lee la [Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md)
2. Aprende a [Acceder a la Papelera](RECYCLE_BIN_USER_GUIDE.md#acceso-a-la-papelera)
3. Practica [Restaurar Registros](RECYCLE_BIN_USER_GUIDE.md#restaurar-registros)

### Nuevo Administrador
1. Lee la [Guía de Configuración](RECYCLE_BIN_CONFIGURATION.md)
2. Configura [Variables de Entorno](RECYCLE_BIN_CONFIGURATION.md#variables-de-entorno)
3. Aprende los [Comandos Básicos](RECYCLE_BIN_COMMANDS.md)

### Nuevo Desarrollador
1. Lee la [Guía de Inicio Rápido](RECYCLE_BIN_QUICK_START.md)
2. Revisa la [Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md)
3. Explora los [Ejemplos de Código](RECYCLE_BIN_TECHNICAL_GUIDE.md#integración-con-módulos-existentes)

## 📋 Tareas Comunes

### Como Usuario

| Tarea | Documentación |
|-------|---------------|
| Ver elementos eliminados | [Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md#ver-elementos-en-la-papelera) |
| Restaurar un registro | [Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md#restauración-individual) |
| Buscar en la papelera | [Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md#búsqueda-por-texto) |
| Entender notificaciones | [Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md#notificaciones) |

### Como Administrador

| Tarea | Documentación |
|-------|---------------|
| Configurar retención | [Comandos](RECYCLE_BIN_COMMANDS.md#setup_recycle_bin) |
| Limpiar papelera | [Comandos](RECYCLE_BIN_COMMANDS.md#cleanup_recycle_bin) |
| Generar reportes | [Comandos](RECYCLE_BIN_COMMANDS.md#generate_recycle_report) |
| Asignar permisos | [Comandos](RECYCLE_BIN_COMMANDS.md#assign_recycle_permissions) |
| Cambiar código de seguridad | [Configuración](RECYCLE_BIN_CONFIGURATION.md#permanent_delete_code) |

### Como Desarrollador

| Tarea | Documentación |
|-------|---------------|
| Integrar soft delete | [Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md#extender-un-modelo-con-soft-delete) |
| Usar el servicio | [Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md#recyclebinservice) |
| Crear tests | [Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md#testing) |
| Optimizar queries | [Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md#optimización-de-performance) |

## 🔍 Búsqueda Rápida

### Conceptos Clave

- **Soft Delete**: [Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md#softdeletemixin-modelo-base)
- **RecycleBin**: [Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md#recyclebin-model)
- **Código de Seguridad**: [Configuración](RECYCLE_BIN_CONFIGURATION.md#permanent_delete_code)
- **Eliminación Automática**: [Comandos](RECYCLE_BIN_COMMANDS.md#cleanup_recycle_bin)
- **Auditoría**: [Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md#deletionauditlog-model)

### Comandos

- **cleanup_recycle_bin**: [Documentación](RECYCLE_BIN_COMMANDS.md#cleanup_recycle_bin)
- **setup_recycle_bin**: [Documentación](RECYCLE_BIN_COMMANDS.md#setup_recycle_bin)
- **generate_recycle_report**: [Documentación](RECYCLE_BIN_COMMANDS.md#generate_recycle_report)
- **restore_from_backup**: [Documentación](RECYCLE_BIN_COMMANDS.md#restore_from_backup)
- **update_retention_policies**: [Documentación](RECYCLE_BIN_COMMANDS.md#update_retention_policies)

### Configuraciones

- **Variables de Entorno**: [Configuración](RECYCLE_BIN_CONFIGURATION.md#variables-de-entorno)
- **Celery**: [Configuración](RECYCLE_BIN_CONFIGURATION.md#configuración-de-celery-beat)
- **Email**: [Configuración](RECYCLE_BIN_CONFIGURATION.md#configuración-de-notificaciones)
- **Caché**: [Configuración](RECYCLE_BIN_CONFIGURATION.md#configuración-de-caché)
- **Seguridad**: [Configuración](RECYCLE_BIN_CONFIGURATION.md#configuración-de-seguridad)

## 🆘 Solución de Problemas

### Problemas Comunes

| Problema | Solución |
|----------|----------|
| No puedo restaurar | [Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md#no-puedo-restaurar-un-registro) |
| No recibo notificaciones | [Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md#no-recibo-notificaciones) |
| Código no funciona | [Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md#el-código-de-seguridad-no-funciona) |
| Celery no inicia | [Inicio Rápido](RECYCLE_BIN_QUICK_START.md#problema-celery-no-inicia) |
| Performance lenta | [Guía Técnica](RECYCLE_BIN_TECHNICAL_GUIDE.md#problema-performance-lenta-en-listados) |

### Troubleshooting Detallado

- [Troubleshooting de Usuario](RECYCLE_BIN_USER_GUIDE.md#solución-de-problemas)
- [Troubleshooting de Configuración](RECYCLE_BIN_CONFIGURATION.md#troubleshooting-de-configuración)
- [Troubleshooting Técnico](RECYCLE_BIN_TECHNICAL_GUIDE.md#troubleshooting)
- [Troubleshooting de Inicio Rápido](RECYCLE_BIN_QUICK_START.md#troubleshooting-rápido)

## 📊 Diagramas y Visuales

- [Arquitectura del Sistema](RECYCLE_BIN_TECHNICAL_GUIDE.md#arquitectura-general)
- [Flujo de Datos](RECYCLE_BIN_TECHNICAL_GUIDE.md#flujo-de-datos)
- [Modelos de Datos](RECYCLE_BIN_TECHNICAL_GUIDE.md#modelos-de-datos)

## 🔗 Enlaces Útiles

### Documentación Externa

- [Django Documentation](https://docs.djangoproject.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Recursos del Proyecto

- **Código Fuente**: `apps/core/`
- **Tests**: `tests/test_recycle_bin*.py`
- **Templates**: `templates/core/recycle_bin_*.html`
- **Comandos**: `apps/core/management/commands/`

## 📝 Glosario

- **Soft Delete**: Eliminación lógica que marca registros como eliminados sin borrarlos físicamente
- **Hard Delete**: Eliminación física permanente de la base de datos
- **RecycleBin**: Modelo que almacena referencias a objetos eliminados
- **Código de Seguridad**: Código requerido para eliminación permanente
- **Retención**: Período que un registro permanece en papelera antes de eliminación automática
- **Auditoría**: Registro de todas las operaciones de eliminación y restauración

## 🎯 Casos de Uso

### Caso 1: Usuario Elimina por Error
1. Usuario elimina una oficina por error
2. Se da cuenta inmediatamente
3. Va a la papelera
4. Busca la oficina
5. La restaura con un clic
6. La oficina vuelve a estar activa

**Documentación**: [Restaurar Registros](RECYCLE_BIN_USER_GUIDE.md#restaurar-registros)

### Caso 2: Limpieza Periódica
1. Administrador revisa papelera mensualmente
2. Identifica registros que ya no se necesitan
3. Verifica que nadie los necesita
4. Elimina permanentemente con código de seguridad
5. Sistema registra la operación en auditoría

**Documentación**: [Eliminación Permanente](RECYCLE_BIN_USER_GUIDE.md#eliminación-permanente)

### Caso 3: Auditoría de Eliminaciones
1. Auditor necesita revisar eliminaciones del mes
2. Genera reporte desde el sistema
3. Revisa estadísticas y detalles
4. Exporta a PDF para documentación
5. Identifica patrones y hace recomendaciones

**Documentación**: [Generar Reportes](RECYCLE_BIN_COMMANDS.md#generate_recycle_report)

### Caso 4: Integración en Nuevo Módulo
1. Desarrollador crea nuevo módulo
2. Extiende modelo con SoftDeleteMixin
3. Actualiza vistas para usar soft delete
4. Configura retención específica
5. Crea tests de integración

**Documentación**: [Integración](RECYCLE_BIN_TECHNICAL_GUIDE.md#integración-con-módulos-existentes)

## 📅 Mantenimiento

### Tareas Diarias
- Revisar logs de Celery
- Verificar ejecución de limpieza automática
- Monitorear intentos fallidos de código

### Tareas Semanales
- Revisar estadísticas de papelera
- Verificar notificaciones enviadas
- Revisar logs de auditoría

### Tareas Mensuales
- Generar reporte mensual
- Revisar políticas de retención
- Actualizar documentación si hay cambios
- Verificar performance del sistema

### Tareas Trimestrales
- Cambiar código de seguridad
- Revisar y actualizar permisos
- Analizar patrones de uso
- Optimizar configuraciones

## 🔐 Seguridad

### Checklist de Seguridad

- [ ] Código de seguridad cambiado del valor por defecto
- [ ] Código de seguridad tiene mínimo 12 caracteres
- [ ] Rate limiting configurado
- [ ] CAPTCHA habilitado
- [ ] Logs de auditoría activos
- [ ] Permisos correctamente asignados
- [ ] Notificaciones de intentos fallidos activas
- [ ] Backups regulares configurados

**Documentación**: [Configuración de Seguridad](RECYCLE_BIN_CONFIGURATION.md#configuración-de-seguridad)

## 📞 Soporte

### Canales de Soporte

- **Email**: soporte@patrimonio.gob
- **Teléfono**: +XXX-XXX-XXXX
- **Documentación**: Esta carpeta `docs/`
- **Issues**: [URL del repositorio]

### Antes de Contactar Soporte

1. Revisa la documentación relevante
2. Busca en la sección de troubleshooting
3. Verifica los logs del sistema
4. Prepara información del error (logs, screenshots)

## 🎓 Capacitación

### Materiales de Capacitación

- [Guía de Usuario](RECYCLE_BIN_USER_GUIDE.md) - Para usuarios finales
- [Guía de Inicio Rápido](RECYCLE_BIN_QUICK_START.md) - Para nuevos desarrolladores
- [Guía de Configuración](RECYCLE_BIN_CONFIGURATION.md) - Para administradores

### Temas de Capacitación Recomendados

1. **Para Usuarios** (1 hora)
   - Introducción al sistema
   - Cómo usar la papelera
   - Restaurar registros
   - Entender notificaciones

2. **Para Administradores** (2 horas)
   - Configuración del sistema
   - Gestión de permisos
   - Comandos de management
   - Generación de reportes

3. **Para Desarrolladores** (4 horas)
   - Arquitectura del sistema
   - Integración con módulos
   - APIs y servicios
   - Testing y debugging

## 📈 Métricas y KPIs

### Métricas Recomendadas

- Tasa de restauración (restauraciones / eliminaciones)
- Tiempo promedio en papelera
- Elementos eliminados por módulo
- Usuarios más activos
- Intentos fallidos de código de seguridad

**Documentación**: [Dashboard de Estadísticas](RECYCLE_BIN_USER_GUIDE.md#dashboard-de-estadísticas)

## 🔄 Actualizaciones

### Historial de Versiones

- **v1.0.0** (2025-01-15): Lanzamiento inicial
  - Soft delete básico
  - Papelera centralizada
  - Eliminación automática
  - Notificaciones
  - Auditoría completa

### Próximas Funcionalidades

- Versionado de objetos
- Papelera compartida
- Reglas de retención avanzadas
- Integración con backup
- Machine learning para predicción

## 📚 Documentos Relacionados

- [README Principal](../README.md)
- [Guía de Instalación](INSTALLATION.md)
- [Guía de Administración](ADMIN_GUIDE.md)
- [Guía de Mantenimiento](MAINTENANCE.md)
- [Gestión de Usuarios](USER_MANAGEMENT.md)

## 🎉 Conclusión

Esta documentación cubre todos los aspectos del Sistema de Papelera de Reciclaje. Si no encuentras lo que buscas, contacta al equipo de soporte.

**¡Gracias por usar el Sistema de Papelera de Reciclaje!**

---

**Última actualización**: 2025-01-15  
**Versión**: 1.0.0  
**Mantenido por**: Equipo de Desarrollo - Patrimonio
