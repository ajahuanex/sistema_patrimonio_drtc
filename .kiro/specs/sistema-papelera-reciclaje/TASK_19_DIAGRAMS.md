# DeletionAuditLog - Diagramas y Visualizaciones

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sistema de Auditoría                         │
│                      DeletionAuditLog                           │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Registra
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                    RecycleBinService                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ soft_delete  │  │   restore    │  │ permanent_delete     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Usa
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                         Vistas                                  │
│  ┌──────────────────┐  ┌────────────────────────────────────┐  │
│  │ recycle_bin_     │  │ recycle_bin_bulk_restore           │  │
│  │ restore          │  │                                    │  │
│  └──────────────────┘  └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Request
                              │
                         ┌────┴────┐
                         │ Usuario │
                         └─────────┘
```

## 🔄 Flujo de Logging Automático

### Soft Delete
```
Usuario → Vista → RecycleBinService.soft_delete_object()
                         │
                         ├─→ obj.soft_delete()
                         │
                         ├─→ RecycleBin.create()
                         │
                         └─→ DeletionAuditLog.log_soft_delete()
                                   │
                                   ├─→ Crear snapshot
                                   ├─→ Registrar contexto (IP, UA)
                                   └─→ Guardar log
```

### Restore
```
Usuario → Vista → RecycleBinService.restore_object()
                         │
                         ├─→ Verificar permisos
                         │
                         ├─→ Validar conflictos
                         │     │
                         │     └─→ Si hay conflicto:
                         │         DeletionAuditLog.log_failed_operation()
                         │
                         ├─→ obj.restore()
                         │
                         ├─→ entry.mark_as_restored()
                         │
                         └─→ DeletionAuditLog.log_restore()
                                   │
                                   ├─→ Guardar estado anterior
                                   ├─→ Registrar contexto
                                   └─→ Guardar log
```

### Permanent Delete
```
Usuario → Vista → RecycleBinService.permanent_delete()
                         │
                         ├─→ Verificar permisos
                         │
                         ├─→ Verificar código de seguridad
                         │     │
                         │     └─→ Si incorrecto:
                         │         SecurityCodeAttempt.record_attempt()
                         │
                         ├─→ DeletionAuditLog.log_permanent_delete()
                         │     │
                         │     └─→ Crear snapshot COMPLETO
                         │
                         ├─→ obj.hard_delete()
                         │
                         └─→ entry.delete()
```

## 📊 Estructura del Modelo

```
DeletionAuditLog
├── Identificación
│   ├── id (PK)
│   ├── action (8 opciones)
│   └── timestamp (indexed)
│
├── Usuario y Contexto
│   ├── user (FK → User, PROTECT)
│   ├── ip_address (GenericIPAddress)
│   └── user_agent (Text)
│
├── Objeto Afectado
│   ├── content_type (FK → ContentType)
│   ├── object_id (PositiveInteger)
│   ├── object_repr (CharField)
│   └── module_name (CharField)
│
├── Datos de Auditoría
│   ├── reason (Text)
│   ├── object_snapshot (JSON)
│   ├── previous_state (JSON)
│   └── metadata (JSON)
│
├── Estado de Operación
│   ├── success (Boolean)
│   └── error_message (Text)
│
└── Referencias
    ├── recycle_bin_entry (FK → RecycleBin)
    └── security_code_used (Boolean)
```

## 🗄️ Índices de Base de Datos

```
Índices Creados:
┌────────────────────────────────┬──────────────────────────┐
│ Nombre                         │ Campos                   │
├────────────────────────────────┼──────────────────────────┤
│ deletion_audit_time_idx        │ [timestamp]              │
│ deletion_audit_user_time_idx   │ [user, timestamp]        │
│ deletion_audit_action_time_idx │ [action, timestamp]      │
│ deletion_audit_module_time_idx │ [module_name, timestamp] │
│ deletion_audit_content_idx     │ [content_type, object_id]│
└────────────────────────────────┴──────────────────────────┘

Optimización de Consultas:
• Búsqueda por fecha: O(log n) con índice
• Búsqueda por usuario: O(log n) con índice
• Búsqueda por acción: O(log n) con índice
• Búsqueda por objeto: O(log n) con índice compuesto
```

## 🎯 Tipos de Acciones y Flujos

```
┌─────────────────────────────────────────────────────────────┐
│                    Acciones Normales                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  soft_delete ──────────────────────────────────────────┐    │
│       │                                                │    │
│       ▼                                                │    │
│  [En Papelera]                                         │    │
│       │                                                │    │
│       ├──→ restore ──→ [Activo]                        │    │
│       │                                                │    │
│       └──→ permanent_delete ──→ [Eliminado de BD]      │    │
│                                                        │    │
│  auto_delete ──────────────────→ [Eliminado de BD]     │    │
│                                                        │    │
└────────────────────────────────────────────────────────┘    │
                                                              │
┌─────────────────────────────────────────────────────────────┤
│                  Operaciones en Lote                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  bulk_restore ──→ [Múltiples objetos restaurados]          │
│                                                             │
│  bulk_delete ───→ [Múltiples objetos eliminados]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                                                              │
┌─────────────────────────────────────────────────────────────┤
│                  Operaciones Fallidas                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  failed_restore ──→ [Log de error, objeto sin cambios]     │
│                                                             │
│  failed_delete ───→ [Log de error, objeto sin cambios]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Ciclo de Vida Completo con Auditoría

```
Tiempo ──────────────────────────────────────────────────────→

T0: Objeto Activo
    └─→ [No hay logs]

T1: Soft Delete
    └─→ DeletionAuditLog
        ├─→ action: 'soft_delete'
        ├─→ snapshot: {codigo: 'OF001', nombre: '...'}
        ├─→ user: 'juan'
        ├─→ ip: '192.168.1.100'
        └─→ reason: 'Oficina cerrada'

T2: Objeto en Papelera
    └─→ RecycleBin entry creada

T3: Restore
    └─→ DeletionAuditLog
        ├─→ action: 'restore'
        ├─→ previous_state: {deleted_at: 'T1', deleted_by: 'juan'}
        ├─→ user: 'maria'
        ├─→ ip: '192.168.1.101'
        └─→ reason: 'Reapertura'

T4: Objeto Activo nuevamente
    └─→ RecycleBin entry marcada como restaurada

T5: Soft Delete (segunda vez)
    └─→ DeletionAuditLog
        ├─→ action: 'soft_delete'
        ├─→ user: 'admin'
        └─→ reason: 'Cierre definitivo'

T6: Permanent Delete
    └─→ DeletionAuditLog
        ├─→ action: 'permanent_delete'
        ├─→ snapshot: {codigo: 'OF001', nombre: '...', ...}
        ├─→ user: 'admin'
        ├─→ security_code_used: True
        └─→ reason: 'Eliminación definitiva'

T7: Objeto eliminado de BD
    └─→ Logs preservados permanentemente
        ├─→ Log T1: soft_delete
        ├─→ Log T3: restore
        ├─→ Log T5: soft_delete
        └─→ Log T6: permanent_delete (con snapshot completo)
```

## 🔍 Consultas Optimizadas

```
Consulta por Timestamp (Más Común)
┌─────────────────────────────────────────┐
│ SELECT * FROM deletion_audit_log        │
│ WHERE timestamp >= '2025-01-01'         │
│ ORDER BY timestamp DESC                 │
│ LIMIT 100                               │
└─────────────────────────────────────────┘
         │
         ▼
   [Usa índice: deletion_audit_time_idx]
         │
         ▼
   Resultado en O(log n)


Consulta por Usuario y Fecha
┌─────────────────────────────────────────┐
│ SELECT * FROM deletion_audit_log        │
│ WHERE user_id = 5                       │
│   AND timestamp >= '2025-01-01'         │
│ ORDER BY timestamp DESC                 │
└─────────────────────────────────────────┘
         │
         ▼
   [Usa índice: deletion_audit_user_time_idx]
         │
         ▼
   Resultado en O(log n)


Consulta por Objeto
┌─────────────────────────────────────────┐
│ SELECT * FROM deletion_audit_log        │
│ WHERE content_type_id = 10              │
│   AND object_id = 123                   │
│ ORDER BY timestamp DESC                 │
└─────────────────────────────────────────┘
         │
         ▼
   [Usa índice: deletion_audit_content_idx]
         │
         ▼
   Resultado en O(log n)
```

## 📊 Snapshot de Datos

```
Objeto Original (Oficina)
┌─────────────────────────────────────┐
│ id: 123                             │
│ codigo: 'OF001'                     │
│ nombre: 'Oficina Central'           │
│ direccion: 'Calle Principal 123'    │
│ telefono: '555-1234'                │
│ created_by: User(id=5)              │
│ created_at: datetime(...)           │
│ deleted_at: datetime(...)           │
│ deleted_by: User(id=7)              │
└─────────────────────────────────────┘
         │
         ▼ model_to_dict()
         │
         ▼ Conversión de valores
         │
┌─────────────────────────────────────┐
│ Snapshot en DeletionAuditLog        │
├─────────────────────────────────────┤
│ {                                   │
│   "codigo": "OF001",                │
│   "nombre": "Oficina Central",      │
│   "direccion": "Calle Principal...",│
│   "telefono": "555-1234",           │
│   "created_by": {                   │
│     "id": 5,                        │
│     "repr": "juan"                  │
│   },                                │
│   "created_at": "2025-01-01 10:00", │
│   "deleted_at": "2025-01-05 15:30", │
│   "deleted_by": {                   │
│     "id": 7,                        │
│     "repr": "maria"                 │
│   }                                 │
│ }                                   │
└─────────────────────────────────────┘
```

## 🎨 Visualización de Logs

```
Dashboard de Auditoría
┌────────────────────────────────────────────────────────────┐
│  Logs de Auditoría - Últimas 24 horas                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  🗑️  Eliminación Lógica                                    │
│  ├─ juan eliminó "Oficina Central" (oficinas)             │
│  │  IP: 192.168.1.100 | 2025-01-09 10:30                  │
│  └─ Motivo: Oficina cerrada temporalmente                 │
│                                                            │
│  ♻️  Restauración                                          │
│  ├─ maria restauró "Oficina Central" (oficinas)           │
│  │  IP: 192.168.1.101 | 2025-01-09 14:15                  │
│  └─ Motivo: Reapertura de oficina                         │
│                                                            │
│  ❌  Eliminación Permanente                                │
│  ├─ admin eliminó "Bien #12345" (bienes)                  │
│  │  IP: 192.168.1.102 | 2025-01-09 16:45                  │
│  │  🔒 Código de seguridad usado                          │
│  └─ Motivo: Bien dado de baja definitivamente             │
│                                                            │
│  ⚠️♻️ Restauración Fallida                                 │
│  ├─ pedro intentó restaurar "Catálogo XYZ" (catalogo)     │
│  │  IP: 192.168.1.103 | 2025-01-09 17:20                  │
│  └─ Error: Conflicto - código duplicado                   │
│                                                            │
└────────────────────────────────────────────────────────────┘

Estadísticas
┌────────────────────────────────────────────────────────────┐
│  Por Acción              Por Usuario          Por Módulo   │
│  ├─ Soft Delete: 45      ├─ juan: 23          ├─ oficinas │
│  ├─ Restore: 38          ├─ maria: 18         ├─ bienes   │
│  ├─ Permanent: 12        ├─ admin: 15         └─ catalogo │
│  └─ Failed: 5            └─ pedro: 9                       │
│                                                            │
│  Tasa de Éxito: 95%                                        │
└────────────────────────────────────────────────────────────┘
```

## 🔐 Flujo de Seguridad

```
Eliminación Permanente con Código de Seguridad
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Usuario intenta eliminar permanentemente               │
│         │                                               │
│         ▼                                               │
│  ¿Es administrador?                                     │
│         │                                               │
│    No ──┴──→ [Denegar] ──→ Log: failed_delete          │
│         │                                               │
│    Sí   │                                               │
│         ▼                                               │
│  ¿Usuario bloqueado?                                    │
│         │                                               │
│    Sí ──┴──→ [Denegar] ──→ Mensaje: "Bloqueado X min"  │
│         │                                               │
│    No   │                                               │
│         ▼                                               │
│  Solicitar código de seguridad                          │
│         │                                               │
│         ▼                                               │
│  ¿Código correcto?                                      │
│         │                                               │
│    No ──┴──→ SecurityCodeAttempt.record(success=False) │
│         │    │                                          │
│         │    └──→ ¿3+ intentos? ──→ [Bloquear 30 min]  │
│         │                                               │
│    Sí   │                                               │
│         ▼                                               │
│  SecurityCodeAttempt.record(success=True)               │
│         │                                               │
│         ▼                                               │
│  DeletionAuditLog.log_permanent_delete()                │
│         │                                               │
│         ▼                                               │
│  obj.hard_delete()                                      │
│         │                                               │
│         ▼                                               │
│  [Éxito] ──→ Mensaje: "Eliminado permanentemente"       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 📊 Métricas de Performance

```
Operación                    Tiempo Promedio    Índice Usado
─────────────────────────────────────────────────────────────
Crear log                    < 5ms              N/A
Consulta por timestamp       < 10ms             time_idx
Consulta por usuario         < 10ms             user_time_idx
Consulta por acción          < 10ms             action_time_idx
Consulta por objeto          < 10ms             content_idx
Bulk operation (10 logs)     < 50ms             N/A
Exportar 1000 logs a CSV     < 500ms            time_idx

Tamaño de Datos
─────────────────────────────────────────────────────────────
Log sin snapshot             ~500 bytes
Log con snapshot pequeño     ~2 KB
Log con snapshot completo    ~5-10 KB
1000 logs                    ~2-5 MB
```

---

**Nota:** Estos diagramas son representaciones visuales del sistema. Para detalles técnicos específicos, consulta la documentación completa.
