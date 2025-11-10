# Comandos de Management - Sistema de Papelera de Reciclaje

## Introducción

Este documento describe todos los comandos de management disponibles para administrar el sistema de papelera de reciclaje. Los comandos se ejecutan usando `python manage.py <comando>`.

## Índice de Comandos

1. [cleanup_recycle_bin](#cleanup_recycle_bin) - Limpieza automática de papelera
2. [setup_recycle_bin](#setup_recycle_bin) - Configuración inicial del sistema
3. [generate_recycle_report](#generate_recycle_report) - Generación de reportes
4. [restore_from_backup](#restore_from_backup) - Restauración desde backup
5. [update_retention_policies](#update_retention_policies) - Actualización de políticas
6. [setup_recycle_permissions](#setup_recycle_permissions) - Configuración de permisos
7. [assign_recycle_permissions](#assign_recycle_permissions) - Asignación de permisos
8. [check_suspicious_patterns](#check_suspicious_patterns) - Detección de patrones sospechosos

---

## cleanup_recycle_bin

Limpia automáticamente los registros de la papelera que han excedido su período de retención.

### Ubicación
`apps/core/management/commands/cleanup_recycle_bin.py`

### Sintaxis Básica

```bash
python manage.py cleanup_recycle_bin [opciones]
```

### Opciones

| Opción | Descripción | Valor por Defecto |
|--------|-------------|-------------------|
| `--dry-run` | Simula la limpieza sin eliminar | False |
| `--module <nombre>` | Limpia solo un módulo específico | Todos |
| `--verbose` | Muestra información detallada | False |
| `--force` | Fuerza eliminación sin confirmación | False |
| `--days <número>` | Sobrescribe días de retención | Config |

### Ejemplos de Uso

#### Limpieza Normal
```bash
python manage.py cleanup_recycle_bin
```

#### Modo Dry-Run (Simulación)
```bash
python manage.py cleanup_recycle_bin --dry-run
```
Muestra qué se eliminaría sin hacer cambios reales.

#### Módulo Específico
```bash
python manage.py cleanup_recycle_bin --module=oficinas
```
Limpia solo elementos del módulo de oficinas.

#### Con Verbose
```bash
python manage.py cleanup_recycle_bin --verbose
```
Muestra detalles de cada elemento eliminado.

#### Forzar Limpieza
```bash
python manage.py cleanup_recycle_bin --force
```
No solicita confirmación antes de eliminar.

#### Días Personalizados
```bash
python manage.py cleanup_recycle_bin --days=60
```
Elimina elementos con más de 60 días en papelera.

### Salida Esperada

```
=== Limpieza de Papelera de Reciclaje ===

Configuración:
- Modo: Producción
- Módulos: Todos
- Días de retención: Por configuración

Analizando elementos...
- Oficinas: 5 elementos a eliminar
- Bienes: 12 elementos a eliminar
- Catálogo: 3 elementos a eliminar

Total: 20 elementos serán eliminados permanentemente

¿Continuar? (s/n): s

Eliminando elementos...
✓ Oficina "Oficina Regional Norte" eliminada
✓ Bien "Escritorio #12345" eliminado
...

=== Resumen ===
- Elementos eliminados: 20
- Errores: 0
- Tiempo: 2.5 segundos
```

### Programación Automática

Este comando se ejecuta automáticamente vía Celery:

```python
# En patrimonio/celery.py
app.conf.beat_schedule = {
    'cleanup-recycle-bin': {
        'task': 'patrimonio.celery.cleanup_recycle_bin_task',
        'schedule': crontab(hour=2, minute=0),  # Diario a las 2:00 AM
    },
}
```

### Códigos de Salida

- `0`: Éxito
- `1`: Error general
- `2`: No hay elementos para eliminar

---

## setup_recycle_bin

Configura el sistema de papelera de reciclaje, creando configuraciones iniciales y permisos.

### Ubicación
`apps/core/management/commands/setup_recycle_bin.py`

### Sintaxis Básica

```bash
python manage.py setup_recycle_bin [opciones]
```

### Opciones

| Opción | Descripción | Valor por Defecto |
|--------|-------------|-------------------|
| `--module <nombre>` | Configura módulo específico | Todos |
| `--retention-days <número>` | Días de retención | 30 |
| `--auto-delete` | Habilita eliminación automática | True |
| `--no-auto-delete` | Deshabilita eliminación automática | - |
| `--setup-permissions` | Configura permisos del sistema | False |
| `--reset` | Resetea configuración existente | False |

### Ejemplos de Uso

#### Configuración Inicial Completa
```bash
python manage.py setup_recycle_bin
```
Crea configuraciones para todos los módulos con valores por defecto.

#### Módulo Específico
```bash
python manage.py setup_recycle_bin --module=bienes --retention-days=60
```
Configura el módulo de bienes con 60 días de retención.

#### Deshabilitar Eliminación Automática
```bash
python manage.py setup_recycle_bin --module=oficinas --no-auto-delete
```

#### Configurar Permisos
```bash
python manage.py setup_recycle_bin --setup-permissions
```
Crea todos los permisos necesarios en el sistema.

#### Resetear Configuración
```bash
python manage.py setup_recycle_bin --reset
```
Elimina y recrea todas las configuraciones.

### Salida Esperada

```
=== Configuración de Papelera de Reciclaje ===

Creando configuraciones...
✓ Módulo 'oficinas' configurado (30 días)
✓ Módulo 'bienes' configurado (30 días)
✓ Módulo 'catalogo' configurado (30 días)

Configurando permisos...
✓ Permiso 'view_recycle_bin' creado
✓ Permiso 'restore_items' creado
✓ Permiso 'permanent_delete_items' creado

=== Configuración Completada ===
```

---

## generate_recycle_report

Genera reportes detallados de auditoría de la papelera de reciclaje.

### Ubicación
`apps/core/management/commands/generate_recycle_report.py`

### Sintaxis Básica

```bash
python manage.py generate_recycle_report [opciones]
```

### Opciones

| Opción | Descripción | Valor por Defecto |
|--------|-------------|-------------------|
| `--start-date <fecha>` | Fecha inicial (YYYY-MM-DD) | Hace 30 días |
| `--end-date <fecha>` | Fecha final (YYYY-MM-DD) | Hoy |
| `--format <formato>` | Formato: pdf, excel, csv, json | pdf |
| `--output <archivo>` | Archivo de salida | auto |
| `--module <nombre>` | Filtrar por módulo | Todos |
| `--user <username>` | Filtrar por usuario | Todos |
| `--include-stats` | Incluir estadísticas | True |
| `--include-charts` | Incluir gráficos (solo PDF) | True |

### Ejemplos de Uso

#### Reporte Básico
```bash
python manage.py generate_recycle_report
```
Genera reporte PDF del último mes.

#### Período Específico
```bash
python manage.py generate_recycle_report \
  --start-date=2025-01-01 \
  --end-date=2025-01-31
```

#### Formato Excel
```bash
python manage.py generate_recycle_report \
  --format=excel \
  --output=reporte_enero.xlsx
```

#### Módulo Específico
```bash
python manage.py generate_recycle_report \
  --module=bienes \
  --format=csv
```

#### Usuario Específico
```bash
python manage.py generate_recycle_report \
  --user=admin \
  --include-stats
```

#### Reporte Completo
```bash
python manage.py generate_recycle_report \
  --start-date=2025-01-01 \
  --end-date=2025-12-31 \
  --format=pdf \
  --output=reporte_anual_2025.pdf \
  --include-stats \
  --include-charts
```

### Contenido del Reporte

#### Sección 1: Resumen Ejecutivo
- Total de eliminaciones
- Total de restauraciones
- Eliminaciones permanentes
- Tasa de restauración

#### Sección 2: Análisis por Módulo
- Distribución de eliminaciones
- Módulos más activos
- Tendencias por módulo

#### Sección 3: Análisis por Usuario
- Usuarios más activos
- Patrones de eliminación
- Usuarios con más restauraciones

#### Sección 4: Timeline
- Gráfico de eliminaciones por día
- Picos de actividad
- Tendencias temporales

#### Sección 5: Detalles
- Lista completa de operaciones
- Información de cada registro
- Contexto de eliminación

### Salida Esperada

```
=== Generación de Reporte de Papelera ===

Parámetros:
- Período: 2025-01-01 a 2025-01-31
- Formato: PDF
- Módulos: Todos
- Usuarios: Todos

Recopilando datos...
✓ 150 eliminaciones encontradas
✓ 45 restauraciones encontradas
✓ 20 eliminaciones permanentes

Generando estadísticas...
✓ Análisis por módulo completado
✓ Análisis por usuario completado
✓ Timeline generado

Creando gráficos...
✓ Gráfico de distribución
✓ Gráfico de tendencias
✓ Gráfico de usuarios

Generando PDF...
✓ Reporte guardado en: reportes/recycle_bin_2025-01.pdf

=== Reporte Generado Exitosamente ===
Archivo: reportes/recycle_bin_2025-01.pdf
Tamaño: 2.5 MB
Páginas: 15
```

---

## restore_from_backup

Restaura objetos desde archivos de backup en casos de emergencia.

### Ubicación
`apps/core/management/commands/restore_from_backup.py`

### Sintaxis Básica

```bash
python manage.py restore_from_backup [opciones]
```

### Opciones

| Opción | Descripción | Requerido |
|--------|-------------|-----------|
| `--backup-file <archivo>` | Archivo de backup JSON | Sí* |
| `--object-id <id>` | ID del objeto a restaurar | Sí* |
| `--content-type <tipo>` | Tipo de contenido | Sí* |
| `--dry-run` | Simular restauración | No |
| `--force` | Forzar sin validaciones | No |

*Requerido uno de: backup-file O (object-id + content-type)

### Ejemplos de Uso

#### Desde Archivo de Backup
```bash
python manage.py restore_from_backup \
  --backup-file=backups/backup_2025-01-15.json
```

#### Objeto Específico
```bash
python manage.py restore_from_backup \
  --object-id=123 \
  --content-type=oficina
```

#### Modo Dry-Run
```bash
python manage.py restore_from_backup \
  --backup-file=backup.json \
  --dry-run
```

#### Forzar Restauración
```bash
python manage.py restore_from_backup \
  --object-id=456 \
  --content-type=bien \
  --force
```

### Formato de Archivo de Backup

```json
{
  "version": "1.0",
  "timestamp": "2025-01-15T10:30:00Z",
  "objects": [
    {
      "content_type": "oficina",
      "object_id": 123,
      "data": {
        "nombre": "Oficina Central",
        "codigo": "OC-001",
        "direccion": "Calle Principal 123"
      },
      "relations": {
        "bienes": [1, 2, 3]
      }
    }
  ]
}
```

### Salida Esperada

```
=== Restauración desde Backup ===

Leyendo archivo: backups/backup_2025-01-15.json
✓ Archivo válido
✓ 5 objetos encontrados

Validando objetos...
✓ Oficina #123: OK
✓ Bien #456: OK
⚠ Catálogo #789: Conflicto detectado

Resolviendo conflictos...
? Catálogo #789 ya existe. ¿Sobrescribir? (s/n): s

Restaurando objetos...
✓ Oficina #123 restaurada
✓ Bien #456 restaurado
✓ Catálogo #789 restaurado

=== Restauración Completada ===
- Objetos restaurados: 3
- Conflictos resueltos: 1
- Errores: 0
```

---

## update_retention_policies

Actualiza las políticas de retención de forma masiva.

### Ubicación
`apps/core/management/commands/update_retention_policies.py`

### Sintaxis Básica

```bash
python manage.py update_retention_policies [opciones]
```

### Opciones

| Opción | Descripción | Valor por Defecto |
|--------|-------------|-------------------|
| `--module <nombre>` | Módulo a actualizar | Todos |
| `--retention-days <número>` | Nuevos días de retención | - |
| `--enable-auto-delete` | Habilitar eliminación automática | - |
| `--disable-auto-delete` | Deshabilitar eliminación automática | - |
| `--warning-days <número>` | Días para primera advertencia | 7 |
| `--final-warning-days <número>` | Días para advertencia final | 1 |
| `--apply` | Aplicar cambios (sin esto solo muestra) | False |

### Ejemplos de Uso

#### Ver Políticas Actuales
```bash
python manage.py update_retention_policies
```

#### Actualizar Días de Retención
```bash
python manage.py update_retention_policies \
  --module=bienes \
  --retention-days=90 \
  --apply
```

#### Habilitar Eliminación Automática
```bash
python manage.py update_retention_policies \
  --module=oficinas \
  --enable-auto-delete \
  --apply
```

#### Actualización Masiva
```bash
python manage.py update_retention_policies \
  --retention-days=60 \
  --warning-days=10 \
  --final-warning-days=2 \
  --apply
```

### Salida Esperada

```
=== Políticas de Retención Actuales ===

Módulo: oficinas
- Días de retención: 30
- Eliminación automática: Habilitada
- Advertencia: 7 días antes
- Advertencia final: 1 día antes

Módulo: bienes
- Días de retención: 30
- Eliminación automática: Habilitada
- Advertencia: 7 días antes
- Advertencia final: 1 día antes

=== Cambios Propuestos ===

Módulo: bienes
- Días de retención: 30 → 90
- Sin otros cambios

¿Aplicar cambios? (s/n): s

✓ Políticas actualizadas exitosamente
```

---

## setup_recycle_permissions

Configura los permisos del sistema de papelera.

### Ubicación
`apps/core/management/commands/setup_recycle_permissions.py`

### Sintaxis Básica

```bash
python manage.py setup_recycle_permissions [opciones]
```

### Opciones

| Opción | Descripción | Valor por Defecto |
|--------|-------------|-------------------|
| `--reset` | Eliminar y recrear permisos | False |
| `--verbose` | Mostrar detalles | False |

### Ejemplos de Uso

#### Configuración Inicial
```bash
python manage.py setup_recycle_permissions
```

#### Resetear Permisos
```bash
python manage.py setup_recycle_permissions --reset
```

### Permisos Creados

- `view_recycle_bin`: Ver papelera de reciclaje
- `restore_items`: Restaurar elementos
- `restore_own_items`: Restaurar propios elementos
- `restore_others_items`: Restaurar elementos de otros
- `permanent_delete_items`: Eliminación permanente
- `view_audit_logs`: Ver logs de auditoría
- `export_audit_logs`: Exportar logs de auditoría
- `configure_recycle_bin`: Configurar sistema

---

## assign_recycle_permissions

Asigna permisos de papelera a usuarios o grupos.

### Ubicación
`apps/core/management/commands/assign_recycle_permissions.py`

### Sintaxis Básica

```bash
python manage.py assign_recycle_permissions [opciones]
```

### Opciones

| Opción | Descripción | Requerido |
|--------|-------------|-----------|
| `--user <username>` | Usuario a asignar | Sí* |
| `--group <nombre>` | Grupo a asignar | Sí* |
| `--role <rol>` | Rol predefinido | No |
| `--permissions <lista>` | Permisos específicos | No |

*Requerido uno de: user O group

### Roles Predefinidos

- `admin`: Todos los permisos
- `funcionario`: Ver y restaurar propios
- `auditor`: Ver y exportar auditoría

### Ejemplos de Uso

#### Asignar Rol a Usuario
```bash
python manage.py assign_recycle_permissions \
  --user=juan.perez \
  --role=admin
```

#### Asignar Rol a Grupo
```bash
python manage.py assign_recycle_permissions \
  --group=Administradores \
  --role=admin
```

#### Permisos Específicos
```bash
python manage.py assign_recycle_permissions \
  --user=maria.lopez \
  --permissions=view_recycle_bin,restore_own_items
```

---

## check_suspicious_patterns

Detecta patrones sospechosos en operaciones de papelera.

### Ubicación
`apps/core/management/commands/check_suspicious_patterns.py`

### Sintaxis Básica

```bash
python manage.py check_suspicious_patterns [opciones]
```

### Opciones

| Opción | Descripción | Valor por Defecto |
|--------|-------------|-------------------|
| `--days <número>` | Días a analizar | 7 |
| `--threshold <número>` | Umbral de alertas | 10 |
| `--send-alerts` | Enviar alertas por email | False |
| `--verbose` | Mostrar detalles | False |

### Patrones Detectados

1. **Eliminaciones Masivas**: Más de X eliminaciones en Y tiempo
2. **Intentos Fallidos**: Múltiples intentos de código incorrecto
3. **Horarios Inusuales**: Operaciones fuera de horario laboral
4. **Usuarios Sospechosos**: Patrones anómalos por usuario

### Ejemplos de Uso

#### Análisis Básico
```bash
python manage.py check_suspicious_patterns
```

#### Análisis Extendido
```bash
python manage.py check_suspicious_patterns \
  --days=30 \
  --threshold=5 \
  --send-alerts
```

### Salida Esperada

```
=== Análisis de Patrones Sospechosos ===

Período: Últimos 7 días
Umbral: 10 operaciones

Analizando...

⚠ ALERTA: Eliminaciones masivas detectadas
- Usuario: juan.perez
- Fecha: 2025-01-15 02:30 AM
- Cantidad: 50 eliminaciones en 5 minutos

⚠ ALERTA: Intentos fallidos de código
- Usuario: maria.lopez
- Fecha: 2025-01-16 11:45 PM
- Intentos: 5 intentos fallidos

=== Resumen ===
- Alertas generadas: 2
- Usuarios afectados: 2
- Acciones recomendadas: Revisar manualmente

Alertas enviadas a: admin@patrimonio.gob
```

---

## Programación de Comandos

### Usando Cron (Linux/Mac)

```bash
# Editar crontab
crontab -e

# Limpieza diaria a las 2 AM
0 2 * * * cd /path/to/project && python manage.py cleanup_recycle_bin

# Reporte semanal los lunes a las 8 AM
0 8 * * 1 cd /path/to/project && python manage.py generate_recycle_report --format=pdf

# Verificación de patrones diaria a las 9 AM
0 9 * * * cd /path/to/project && python manage.py check_suspicious_patterns --send-alerts
```

### Usando Task Scheduler (Windows)

```batch
REM Crear tarea programada
schtasks /create /tn "Limpieza Papelera" /tr "python manage.py cleanup_recycle_bin" /sc daily /st 02:00
```

### Usando Celery Beat (Recomendado)

```python
# En patrimonio/celery.py
app.conf.beat_schedule = {
    'cleanup-recycle-bin': {
        'task': 'patrimonio.celery.cleanup_recycle_bin_task',
        'schedule': crontab(hour=2, minute=0),
    },
    'send-recycle-warnings': {
        'task': 'patrimonio.celery.send_recycle_warnings_task',
        'schedule': crontab(hour=9, minute=0),
    },
    'check-suspicious-patterns': {
        'task': 'patrimonio.celery.check_suspicious_patterns_task',
        'schedule': crontab(hour=9, minute=30),
    },
}
```

## Troubleshooting

### Error: "No module named 'apps.core'"

**Solución**: Asegúrate de estar en el directorio raíz del proyecto.

### Error: "Permission denied"

**Solución**: Ejecuta con permisos adecuados o como superusuario.

### Error: "Database locked"

**Solución**: Asegúrate de que no hay otras operaciones en curso.

### Comando no responde

**Solución**: Verifica logs en `logs/django.log` para más detalles.

## Mejores Prácticas

1. **Siempre usa --dry-run primero** para operaciones destructivas
2. **Programa comandos en horarios de baja actividad**
3. **Monitorea logs después de ejecuciones automáticas**
4. **Mantén backups antes de operaciones masivas**
5. **Documenta cambios en políticas de retención**

## Referencias

- Ver `RECYCLE_BIN_TECHNICAL_GUIDE.md` para detalles técnicos
- Ver `RECYCLE_BIN_USER_GUIDE.md` para guía de usuario
- Ver código fuente en `apps/core/management/commands/`
