# Implementation Plan - Sistema de Papelera de Reciclaje

## Fase 1: Infraestructura Base de Soft Delete

- [x] 1. Crear SoftDeleteMixin y Manager personalizado










  - Implementar clase SoftDeleteMixin con campos deleted_at, deleted_by, deletion_reason
  - Crear SoftDeleteManager que excluya automáticamente registros eliminados
  - Implementar métodos soft_delete(), restore(), hard_delete() e is_deleted
  - Crear tests unitarios para validar funcionalidad del mixin
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Crear modelo RecycleBin centralizado















  - Implementar modelo RecycleBin con GenericForeignKey para cualquier objeto
  - Agregar campos para metadatos (object_repr, module_name, auto_delete_at)
  - Incluir campos de auditoría (deleted_by, restored_by, timestamps)
  - Crear índices para optimizar consultas frecuentes
  - _Requirements: 2.1, 2.2, 6.1_

- [x] 3. Implementar RecycleBinConfig para configuración por módulo





  - Crear modelo RecycleBinConfig con retention_days, auto_delete_enabled
  - Implementar campos de permisos (can_restore_own, can_restore_others)
  - Crear comando de management para configuración inicial
  - Agregar validaciones para configuraciones
  - _Requirements: 10.1, 10.2, 10.3_

- [x] 4. Crear RecycleBinService para operaciones centralizadas




  - Implementar método soft_delete_object() que cree entrada en RecycleBin
  - Crear método restore_object() con validaciones de conflictos
  - Implementar permanent_delete() con validación de código de seguridad
  - Agregar método auto_cleanup() para eliminación automática
  - _Requirements: 3.1, 3.2, 4.1, 4.2, 5.1_

- [x] 5. Extender BaseModel con SoftDeleteMixin










  - Modificar apps/core/models.py para incluir SoftDeleteMixin en BaseModel
  - Crear migración para agregar campos de soft delete a modelos existentes
  - Actualizar __str__ y métodos existentes para manejar soft delete
  - Verificar compatibilidad con código existente
  - _Requirements: 9.1, 9.2_

## Fase 2: Integración con Modelos Existentes

- [x] 6. Integrar soft delete en modelo Oficina





  - Verificar que Oficina herede correctamente de BaseModel actualizado
  - Sobrescribir método delete() para usar soft_delete automáticamente
  - Actualizar método puede_eliminarse() para considerar soft delete
  - Crear tests específicos para soft delete de oficinas
  - _Requirements: 1.1, 9.3_

- [x] 7. Integrar soft delete en modelo BienPatrimonial





  - Actualizar modelo BienPatrimonial para usar soft delete
  - Manejar relaciones con oficinas eliminadas lógicamente
  - Actualizar consultas existentes para excluir bienes eliminados
  - Crear validaciones para cascada de eliminación
  - _Requirements: 1.4, 9.3_

- [x] 8. Integrar soft delete en modelo Catalogo





  - Implementar soft delete en modelo Catalogo
  - Validar que bienes no queden huérfanos al eliminar catálogo
  - Actualizar importaciones para manejar catálogos eliminados
  - Crear tests de integridad referencial
  - _Requirements: 1.4, 9.3_

- [x] 9. Actualizar vistas existentes para usar soft delete





  - Modificar vistas de eliminación en apps/oficinas/views.py
  - Actualizar vistas de bienes para usar soft delete
  - Modificar vistas de catálogo para eliminación lógica
  - Mantener compatibilidad con interfaces existentes
  - _Requirements: 9.1, 9.2_

## Fase 3: Interfaz de Papelera Centralizada

- [x] 10. Crear vistas principales de papelera





  - Implementar RecycleBinListView con paginación y filtros
  - Crear RecycleBinDetailView para vista previa de objetos eliminados
  - Implementar RestoreView para restauración individual
  - Agregar BulkRestoreView para operaciones en lote
  - _Requirements: 2.1, 2.2, 3.1, 7.1_

- [x] 11. Implementar sistema de filtros avanzados





  - Crear filtros por módulo (oficinas, bienes, catálogo)
  - Implementar filtro por fecha de eliminación (rango)
  - Agregar filtro por usuario que eliminó
  - Crear filtro por tiempo restante antes de eliminación automática
  - _Requirements: 2.3, 2.4_

- [x] 12. Crear formularios de restauración y eliminación





  - Implementar RestoreForm con validación de conflictos
  - Crear PermanentDeleteForm con campo de código de seguridad
  - Agregar BulkOperationForm para operaciones múltiples
  - Implementar validaciones JavaScript en tiempo real
  - _Requirements: 3.3, 3.4, 4.3, 7.4_

- [x] 13. Desarrollar templates de papelera





  - Crear template recycle_bin/list.html con tabla responsive
  - Implementar recycle_bin/detail.html con vista previa de datos
  - Crear modales para confirmación de operaciones
  - Agregar iconografía intuitiva y estados visuales
  - _Requirements: 7.1, 7.2, 7.4_

- [x] 14. Implementar eliminación permanente con código de seguridad





  - Crear vista PermanentDeleteView con validación de código
  - Implementar validación contra variable PERMANENT_DELETE_CODE
  - Agregar logging de intentos de uso del código
  - Crear sistema de bloqueo temporal tras intentos fallidos
  - _Requirements: 4.1, 4.2, 4.3, 8.4_

## Fase 4: Automatización y Notificaciones

- [x] 15. Implementar eliminación automática por tiempo





  - Crear comando de management cleanup_recycle_bin
  - Implementar lógica de eliminación basada en auto_delete_at
  - Agregar configuración de días de retención por módulo
  - Crear tarea de Celery para ejecución automática
  - _Requirements: 5.1, 5.2, 5.5_

- [x] 16. Sistema de notificaciones de advertencia





  - Implementar notificación 7 días antes de eliminación automática
  - Crear notificación final 1 día antes de eliminación
  - Agregar templates de email para notificaciones
  - Implementar sistema de preferencias de notificación por usuario
  - _Requirements: 5.3, 5.4_

- [x] 17. Crear dashboard de estadísticas de papelera





  - Implementar vista de estadísticas con gráficos
  - Mostrar elementos por módulo, usuario y tiempo
  - Agregar métricas de restauraciones vs eliminaciones permanentes
  - Crear exportación de reportes de papelera
  - _Requirements: 2.2, 6.4_

- [x] 18. Comandos de management para administración




  - Crear comando setup_recycle_bin para configuración inicial
  - Implementar comando restore_from_backup para emergencias
  - Agregar comando generate_recycle_report para auditoría
  - Crear comando update_retention_policies para cambios masivos
  - _Requirements: 10.4, 6.4_

## Fase 5: Auditoría y Seguridad Completa

- [x] 19. Implementar DeletionAuditLog completo








  - Crear modelo DeletionAuditLog con todas las acciones
  - Implementar logging automático en todas las operaciones
  - Agregar campos de contexto (IP, User-Agent, timestamp)
  - Crear snapshot de datos del objeto antes de eliminación permanente
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 20. Sistema de permisos granular





  - Implementar permisos específicos (can_view_recycle_bin, can_restore_items)
  - Crear grupos de permisos por rol (administrador, funcionario, auditor)
  - Agregar validaciones de permisos en todas las vistas
  - Implementar segregación de datos por usuario
  - _Requirements: 8.1, 8.2, 8.3, 2.6_

- [x] 21. Protección contra ataques de seguridad








  - Implementar rate limiting para intentos de código de seguridad
  - Agregar CAPTCHA después de múltiples intentos fallidos
  - Crear sistema de bloqueo temporal de usuarios
  - Implementar logging detallado de intentos de acceso no autorizado
  - _Requirements: 8.4, 4.4_

- [x] 22. Crear reportes de auditoría de eliminaciones





  - Implementar vista de reportes de auditoría con filtros avanzados
  - Crear exportación de logs de auditoría a PDF y Excel
  - Agregar gráficos de tendencias de eliminaciones por período
  - Implementar alertas automáticas para patrones sospechosos
  - _Requirements: 6.4, 6.1_

- [x] 23. Optimizaciones de rendimiento y caché





  - Implementar caché de estadísticas de papelera
  - Optimizar consultas con select_related y prefetch_related
  - Agregar índices de base de datos para consultas frecuentes
  - Crear sistema de paginación eficiente para grandes volúmenes
  - _Requirements: Performance Optimizations_
- [x] 24. Tests de integración y seguridad completos
  - Crear test suite completo para todos los componentes
  - Implementar tests de carga para operaciones masivas
  - Agregar tests de seguridad para validar controles de acceso
  - Crear tests de regresión para mantener compatibilidad
  - _Requirements: Testing Strategy_

## Fase 6: Integración Final y Documentación

- [x] 25. Integrar papelera en navegación principal
  - Agregar enlace a papelera en menú principal del sistema
  - Crear badges con contadores de elementos en papelera
  - Implementar notificaciones en tiempo real de elementos próximos a eliminarse
  - Agregar accesos rápidos desde listados de cada módulo
  - _Requirements: 7.1, 9.1_

- [x] 26. Configurar tareas de Celery para automatización









  - Crear tarea periódica de Celery para ejecutar cleanup_recycle_bin automáticamente
  - Implementar tarea de Celery para envío de notificaciones de advertencia (7 días antes)
  - Implementar tarea de Celery para notificaciones finales (1 día antes)
  - Agregar configuración de schedule en celery.py usando celery beat
  - Configurar CELERY_BEAT_SCHEDULE con las tareas periódicas
  - Crear tests para verificar ejecución de tareas periódicas
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 27. Crear documentación completa del sistema





  - Escribir guía de usuario para operaciones de papelera
  - Crear documentación técnica para desarrolladores
  - Documentar comandos de management disponibles
  - Agregar ejemplos de configuración y uso avanzado
  - Documentar variables de entorno necesarias
  - _Requirements: Documentation_

- [x] 28. Configurar variables de entorno de producción





  - Agregar PERMANENT_DELETE_CODE a .env.prod.example con valor de ejemplo
  - Agregar PERMANENT_DELETE_CODE a settings.py para leerlo desde entorno
  - Documentar RECAPTCHA_PUBLIC_KEY y RECAPTCHA_PRIVATE_KEY para CAPTCHA
  - Agregar configuración de Celery Beat para tareas periódicas
  - Documentar todas las variables de configuración en .env.prod.example
  - Crear guía de configuración para deployment en documentación
  - _Requirements: 4.2, 10.4_

- [x] 29. Realizar pruebas finales de integración





  - Ejecutar suite completo de tests en ambiente de desarrollo
  - Validar flujos end-to-end de eliminación y restauración
  - Verificar funcionamiento de notificaciones
  - Probar eliminación automática con datos de prueba
  - Validar permisos y seguridad en diferentes roles
  - _Requirements: All Requirements Validation_