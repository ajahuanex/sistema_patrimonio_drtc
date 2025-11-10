# Task 18: Comandos de Management - Guía de Uso Detallada

## 📚 Índice

1. [restore_from_backup - Restauración de Emergencia](#restore_from_backup)
2. [generate_recycle_report - Reportes de Auditoría](#generate_recycle_report)
3. [update_retention_policies - Actualización de Políticas](#update_retention_policies)
4. [Escenarios Prácticos](#escenarios-prácticos)
5. [Automatización](#automatización)
6. [Troubleshooting](#troubleshooting)

---

## restore_from_backup

### Descripción
Comando para restaurar elementos eliminados permanentemente usando logs de auditoría como backup de emergencia.

### Cuándo Usar
- Recuperación de datos eliminados accidentalmente
- Restauración después de eliminación automática
- Auditoría de elementos eliminados
- Recuperación de desastres

### Flujo de Trabajo Recomendado

#### 1. Identificar Elementos a Restaurar
```bash
# Listar todos los elementos disponibles
python manage.py restore_from_backup --list-only

# Filtrar por fecha reciente
python manage.py restore_from_backup \
  --date-from=2025-01-09 \
  --list-only

# Filtrar por módulo específico
python manage.py restore_from_backup \
  --module=oficinas \
  --list-only

# Filtrar por usuario
python manage.py restore_from_backup \
  --user=admin \
  --date-from=2025-01-01 \
  --list-only
```

**Salida Ejemplo:**
```
===================================================================
ELEMENTOS DISPONIBLES PARA RESTAURAR:
===================================================================

ID: 123 | 2025-01-09 14:30
  Objeto: Oficina Central - Lima
  Modelo: Oficina
  Módulo: oficinas
  Eliminado por: admin
  Tipo: eliminacion_automatica
  ✓ Tiene snapshot de datos

ID: 124 | 2025-01-09 15:45
  Objeto: Laptop HP ProBook 450
  Modelo: BienPatrimonial
  Módulo: bienes
  Eliminado por: usuario1
  Tipo: eliminacion_manual
  ✓ Tiene snapshot de datos

... y 15 elementos más
===================================================================
```

#### 2. Restaurar Elemento Específico
```bash
# Restaurar por ID de audit log
python manage.py restore_from_backup \
  --audit-log-id=123 \
  --force

# Restaurar y recrear entrada en RecycleBin
python manage.py restore_from_backup \
  --audit-log-id=123 \
  --force \
  --recreate-recycle-entry
```

**Salida Ejemplo:**
```
=== Restauración desde Backup de Emergencia ===
Filtrando por audit log ID: 123

Logs de auditoría encontrados: 1

  ✓ Restaurado: Oficina Central - Lima

==================================================
Elementos restaurados: 1
Errores: 0

=== Restauración completada ===
```

#### 3. Restauración Masiva
```bash
# Restaurar todos los elementos de un período
python manage.py restore_from_backup \
  --date-from=2025-01-09 \
  --date-to=2025-01-09 \
  --module=oficinas \
  --force
```

### Opciones Avanzadas

#### Filtros Combinados
```bash
# Restaurar elementos de un usuario en un módulo específico
python manage.py restore_from_backup \
  --module=bienes \
  --user=usuario1 \
  --date-from=2025-01-01 \
  --force
```

#### Recreación de Entradas
La opción `--recreate-recycle-entry` es útil cuando:
- Quieres mantener historial de restauración
- Necesitas auditoría completa
- El elemento debe pasar por papelera nuevamente

```bash
python manage.py restore_from_backup \
  --audit-log-id=456 \
  --force \
  --recreate-recycle-entry
```

### Limitaciones
- Solo restaura elementos que tienen logs de auditoría
- Requiere snapshot de datos para recreación completa
- No restaura relaciones complejas automáticamente

---

## generate_recycle_report

### Descripción
Genera reportes detallados de auditoría de la papelera en múltiples formatos.

### Cuándo Usar
- Auditorías mensuales/trimestrales
- Análisis de patrones de eliminación
- Reportes para compliance
- Monitoreo de uso del sistema
- Identificación de elementos próximos a eliminarse

### Formatos Disponibles

#### 1. Formato Texto (TXT)
Ideal para: Visualización rápida en consola, emails

```bash
python manage.py generate_recycle_report --format=txt
```

**Salida Ejemplo:**
```
======================================================================
REPORTE DE PAPELERA DE RECICLAJE
======================================================================
Fecha de generación: 2025-01-09T16:30:00

ESTADÍSTICAS GENERALES
----------------------------------------------------------------------
Total de elementos: 45
Elementos activos en papelera: 32
Elementos restaurados: 13
Tasa de restauración: 28.89%
Próximos a eliminarse: 5

ESTADÍSTICAS POR MÓDULO
----------------------------------------------------------------------
  oficinas: 15 total (10 activos, 5 restaurados)
  bienes: 20 total (15 activos, 5 restaurados)
  catalogo: 10 total (7 activos, 3 restaurados)

ESTADÍSTICAS POR USUARIO
----------------------------------------------------------------------
  admin: 20 eliminaciones
  usuario1: 15 eliminaciones
  usuario2: 10 eliminaciones

ELEMENTOS PRÓXIMOS A ELIMINARSE (7 días)
----------------------------------------------------------------------
  Oficina Regional Norte (oficinas) - 2 días restantes
  Laptop Dell Latitude (bienes) - 3 días restantes
  Categoría Obsoleta (catalogo) - 5 días restantes
======================================================================
```

#### 2. Formato JSON
Ideal para: Integración con otros sistemas, análisis programático

```bash
python manage.py generate_recycle_report \
  --format=json \
  --output=reporte.json
```

**Estructura JSON:**
```json
{
  "metadata": {
    "fecha_generacion": "2025-01-09T16:30:00",
    "periodo": {
      "desde": "2025-01-01",
      "hasta": "2025-01-31"
    },
    "filtros": {
      "modulo": "oficinas",
      "usuario": null
    }
  },
  "estadisticas": {
    "total_elementos": 45,
    "elementos_activos": 32,
    "elementos_restaurados": 13,
    "tasa_restauracion": 28.89,
    "por_modulo": [
      {
        "module_name": "oficinas",
        "total": 15,
        "activos": 10,
        "restaurados": 5
      }
    ]
  },
  "elementos": [
    {
      "id": 1,
      "objeto": "Oficina Central",
      "modulo": "oficinas",
      "eliminado_por": "admin",
      "fecha_eliminacion": "2025-01-05T10:00:00",
      "dias_restantes": 25
    }
  ]
}
```

#### 3. Formato CSV
Ideal para: Excel, análisis de datos, reportes ejecutivos

```bash
python manage.py generate_recycle_report \
  --format=csv \
  --output=reporte.csv
```

**Estructura CSV:**
```csv
ESTADÍSTICAS GENERALES
Métrica,Valor
Total Elementos,45
Elementos Activos,32
Elementos Restaurados,13
Tasa Restauración (%),28.89

ESTADÍSTICAS POR MÓDULO
Módulo,Total,Activos,Restaurados
oficinas,15,10,5
bienes,20,15,5
catalogo,10,7,3

ELEMENTOS EN PAPELERA
ID,Objeto,Módulo,Eliminado Por,Fecha Eliminación,Restaurado,Días Restantes
1,Oficina Central,oficinas,admin,2025-01-05,No,25
2,Laptop HP,bienes,usuario1,2025-01-06,No,24
```

### Casos de Uso Específicos

#### 1. Reporte Mensual de Auditoría
```bash
python manage.py generate_recycle_report \
  --date-from=2025-01-01 \
  --date-to=2025-01-31 \
  --format=csv \
  --output=auditoria_enero_2025.csv \
  --audit-logs \
  --include-restored
```

#### 2. Análisis de Patrones por Usuario
```bash
python manage.py generate_recycle_report \
  --user=usuario1 \
  --format=json \
  --output=analisis_usuario1.json
```

#### 3. Monitoreo de Elementos Próximos a Eliminarse
```bash
python manage.py generate_recycle_report \
  --format=txt \
  --statistics-only
```

#### 4. Reporte Ejecutivo
```bash
python manage.py generate_recycle_report \
  --statistics-only \
  --format=json \
  --output=ejecutivo_$(date +%Y%m%d).json
```

#### 5. Reporte Completo con Auditoría
```bash
python manage.py generate_recycle_report \
  --format=json \
  --audit-logs \
  --include-restored \
  --include-deleted \
  --output=reporte_completo.json
```

### Filtros Avanzados

```bash
# Por módulo y período
python manage.py generate_recycle_report \
  --module=bienes \
  --date-from=2025-01-01 \
  --date-to=2025-01-31 \
  --format=csv

# Por usuario y módulo
python manage.py generate_recycle_report \
  --user=admin \
  --module=oficinas \
  --format=txt

# Solo estadísticas sin detalles
python manage.py generate_recycle_report \
  --statistics-only \
  --format=json
```

---

## update_retention_policies

### Descripción
Actualiza políticas de retención de la papelera de forma masiva con validaciones y auditoría.

### Cuándo Usar
- Cambios en políticas organizacionales
- Ajustes estacionales de retención
- Optimización de espacio
- Configuración inicial de módulos nuevos
- Mantenimiento programado

### Flujo de Trabajo Recomendado

#### 1. Revisar Configuración Actual
```bash
# Ver todas las configuraciones
python manage.py update_retention_policies --show-current

# Ver configuración de un módulo
python manage.py update_retention_policies \
  --module=oficinas \
  --show-current
```

**Salida Ejemplo:**
```
======================================================================
CONFIGURACIONES ACTUALES DE PAPELERA
======================================================================

Módulo: oficinas
----------------------------------------------------------------------
  Días de retención: 30
  Eliminación automática: Habilitada
  Días de advertencia: 7
  Días de advertencia final: 1
  Restaurar propios: Habilitado
  Restaurar de otros: Deshabilitado
  Elementos en papelera: 15

Módulo: bienes
----------------------------------------------------------------------
  Días de retención: 30
  Eliminación automática: Habilitada
  Días de advertencia: 7
  Días de advertencia final: 1
  Restaurar propios: Habilitado
  Restaurar de otros: Deshabilitado
  Elementos en papelera: 20
======================================================================
```

#### 2. Previsualizar Cambios (Dry-Run)
```bash
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --warning-days=14 \
  --dry-run
```

**Salida Ejemplo:**
```
=== Actualización de Políticas de Retención ===
MODO DRY-RUN: No se aplicarán cambios

Módulos a actualizar: oficinas, bienes, catalogo, core

Cambios a aplicar:
--------------------------------------------------
  • Días de retención: 90
  • Días de advertencia: 14

[DRY-RUN] Se actualizaría: oficinas
[DRY-RUN] Se actualizaría: bienes
[DRY-RUN] Se actualizaría: catalogo
[DRY-RUN] Se actualizaría: core

==================================================
[DRY-RUN] Se actualizarían 4 configuraciones

=== Actualización completada ===
```

#### 3. Aplicar Cambios
```bash
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --warning-days=14 \
  --force
```

### Escenarios Comunes

#### 1. Aumentar Período de Retención
```bash
# Aumentar a 90 días para todos los módulos
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --update-existing-items \
  --force
```

**Nota:** `--update-existing-items` recalcula las fechas de auto-eliminación de elementos existentes.

#### 2. Configurar Advertencias Personalizadas
```bash
# Advertencias más tempranas
python manage.py update_retention_policies \
  --module=bienes \
  --warning-days=14 \
  --final-warning-days=3 \
  --force
```

#### 3. Deshabilitar Eliminación Automática Temporalmente
```bash
# Útil durante mantenimiento o auditorías
python manage.py update_retention_policies \
  --module=all \
  --disable-auto-delete \
  --force

# Restaurar después
python manage.py update_retention_policies \
  --module=all \
  --enable-auto-delete \
  --force
```

#### 4. Configurar Permisos de Restauración
```bash
# Permitir que usuarios restauren elementos de otros
python manage.py update_retention_policies \
  --module=oficinas \
  --enable-restore-others \
  --force

# Restringir restauración solo a propios elementos
python manage.py update_retention_policies \
  --module=bienes \
  --disable-restore-others \
  --force
```

#### 5. Actualización Completa de Política
```bash
python manage.py update_retention_policies \
  --module=all \
  --retention-days=120 \
  --warning-days=21 \
  --final-warning-days=7 \
  --enable-auto-delete \
  --enable-restore-own \
  --disable-restore-others \
  --update-existing-items \
  --force
```

### Validaciones Automáticas

El comando valida:
- ✅ Días de retención > 0
- ✅ Días de advertencia < Días de retención
- ✅ Días de advertencia final < Días de advertencia
- ✅ No hay flags conflictivos
- ✅ Módulos existen en configuración

**Ejemplo de Error:**
```bash
python manage.py update_retention_policies \
  --module=oficinas \
  --retention-days=30 \
  --warning-days=35 \
  --force

# Error: Los días de advertencia deben ser menores que los días de retención
```

### Auditoría de Cambios

Todos los cambios se registran en AuditLog:
```python
{
    "action": "update",
    "model_name": "RecycleBinConfig",
    "object_repr": "Config oficinas",
    "changes": {
        "old_values": {
            "retention_days": 30,
            "auto_delete_enabled": True
        },
        "new_values": {
            "retention_days": 90,
            "auto_delete_enabled": True
        }
    }
}
```

---

## Escenarios Prácticos

### Escenario 1: Recuperación de Emergencia

**Situación:** Se eliminaron accidentalmente varias oficinas y necesitan restaurarse urgentemente.

```bash
# Paso 1: Identificar eliminaciones recientes
python manage.py restore_from_backup \
  --module=oficinas \
  --date-from=$(date -d "yesterday" +%Y-%m-%d) \
  --list-only

# Paso 2: Restaurar elementos específicos
python manage.py restore_from_backup \
  --audit-log-id=789 \
  --force

# Paso 3: Generar reporte de la operación
python manage.py generate_recycle_report \
  --module=oficinas \
  --include-restored \
  --format=txt
```

### Escenario 2: Auditoría Trimestral

**Situación:** Necesitas generar reportes trimestrales para compliance.

```bash
# Reporte Q1 2025
python manage.py generate_recycle_report \
  --date-from=2025-01-01 \
  --date-to=2025-03-31 \
  --format=csv \
  --output=Q1_2025_auditoria.csv \
  --audit-logs \
  --include-restored

# Reporte ejecutivo
python manage.py generate_recycle_report \
  --date-from=2025-01-01 \
  --date-to=2025-03-31 \
  --statistics-only \
  --format=json \
  --output=Q1_2025_ejecutivo.json
```

### Escenario 3: Cambio de Política Organizacional

**Situación:** La organización decide aumentar el período de retención de 30 a 90 días.

```bash
# Paso 1: Revisar configuración actual
python manage.py update_retention_policies --show-current

# Paso 2: Previsualizar cambios
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --warning-days=14 \
  --final-warning-days=3 \
  --dry-run

# Paso 3: Aplicar cambios
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --warning-days=14 \
  --final-warning-days=3 \
  --update-existing-items \
  --force

# Paso 4: Verificar cambios
python manage.py update_retention_policies --show-current

# Paso 5: Generar reporte de cambios
python manage.py generate_recycle_report \
  --statistics-only \
  --format=txt
```

### Escenario 4: Mantenimiento Programado

**Situación:** Mantenimiento del sistema requiere deshabilitar eliminación automática temporalmente.

```bash
# Antes del mantenimiento
python manage.py update_retention_policies \
  --module=all \
  --disable-auto-delete \
  --force

# Generar backup
python manage.py generate_recycle_report \
  --format=json \
  --output=backup_pre_mantenimiento_$(date +%Y%m%d).json

# Después del mantenimiento
python manage.py update_retention_policies \
  --module=all \
  --enable-auto-delete \
  --force
```

### Escenario 5: Análisis de Patrones de Uso

**Situación:** Analizar qué usuarios eliminan más elementos y en qué módulos.

```bash
# Reporte por usuario
for user in admin usuario1 usuario2; do
  python manage.py generate_recycle_report \
    --user=$user \
    --format=json \
    --output=analisis_${user}.json
done

# Reporte por módulo
for module in oficinas bienes catalogo; do
  python manage.py generate_recycle_report \
    --module=$module \
    --format=csv \
    --output=analisis_${module}.csv
done
```

---

## Automatización

### Scripts de Mantenimiento

#### Script de Backup Diario
```bash
#!/bin/bash
# backup_diario.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/papelera"

# Crear directorio si no existe
mkdir -p $BACKUP_DIR

# Generar reporte diario
python manage.py generate_recycle_report \
  --format=json \
  --output=$BACKUP_DIR/reporte_$DATE.json \
  --audit-logs

echo "Backup completado: $BACKUP_DIR/reporte_$DATE.json"
```

#### Script de Reporte Semanal
```bash
#!/bin/bash
# reporte_semanal.sh

WEEK=$(date +%Y_W%V)
DATE_FROM=$(date -d "7 days ago" +%Y-%m-%d)
DATE_TO=$(date +%Y-%m-%d)

python manage.py generate_recycle_report \
  --date-from=$DATE_FROM \
  --date-to=$DATE_TO \
  --format=csv \
  --output=/reportes/semanal_$WEEK.csv \
  --include-restored

# Enviar por email (opcional)
mail -s "Reporte Semanal Papelera $WEEK" \
  admin@example.com < /reportes/semanal_$WEEK.csv
```

#### Script de Monitoreo
```bash
#!/bin/bash
# monitoreo_papelera.sh

# Generar reporte de estadísticas
python manage.py generate_recycle_report \
  --statistics-only \
  --format=txt

# Verificar elementos próximos a eliminarse
python manage.py generate_recycle_report \
  --format=txt | grep "Próximos a eliminarse"
```

### Cron Jobs

```cron
# Backup diario a las 2 AM
0 2 * * * /path/to/backup_diario.sh

# Reporte semanal los lunes a las 8 AM
0 8 * * 1 /path/to/reporte_semanal.sh

# Monitoreo cada 6 horas
0 */6 * * * /path/to/monitoreo_papelera.sh
```

---

## Troubleshooting

### Problema: No se encuentran elementos para restaurar

**Síntoma:**
```
No se encontraron logs de auditoría que coincidan con los criterios
```

**Soluciones:**
1. Verificar que existen logs de auditoría:
```bash
python manage.py shell
>>> from apps.core.models import AuditLog
>>> AuditLog.objects.filter(action='delete').count()
```

2. Ampliar criterios de búsqueda:
```bash
python manage.py restore_from_backup --list-only
```

3. Verificar fechas:
```bash
python manage.py restore_from_backup \
  --date-from=2025-01-01 \
  --list-only
```

### Problema: Error al generar reporte

**Síntoma:**
```
Error guardando archivo: Permission denied
```

**Soluciones:**
1. Verificar permisos del directorio:
```bash
ls -la /path/to/output/
chmod 755 /path/to/output/
```

2. Usar ruta absoluta:
```bash
python manage.py generate_recycle_report \
  --format=json \
  --output=/tmp/reporte.json
```

3. Generar en consola primero:
```bash
python manage.py generate_recycle_report --format=txt
```

### Problema: Validación falla al actualizar políticas

**Síntoma:**
```
Los días de advertencia deben ser menores que los días de retención
```

**Solución:**
Ajustar valores para que sean coherentes:
```bash
python manage.py update_retention_policies \
  --module=oficinas \
  --retention-days=90 \
  --warning-days=14 \
  --final-warning-days=3 \
  --force
```

### Problema: Elementos no se actualizan

**Síntoma:**
Cambios en retención no afectan elementos existentes.

**Solución:**
Usar flag `--update-existing-items`:
```bash
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --update-existing-items \
  --force
```

### Problema: Comando requiere confirmación

**Síntoma:**
```
Use --force para confirmar la operación
```

**Solución:**
Agregar flag `--force`:
```bash
python manage.py <comando> --force
```

O usar `--dry-run` para previsualizar:
```bash
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --dry-run
```

---

## Mejores Prácticas

1. **Siempre usar --dry-run primero** al actualizar políticas
2. **Generar backups** antes de cambios importantes
3. **Documentar cambios** en políticas de retención
4. **Automatizar reportes** periódicos
5. **Monitorear elementos próximos** a eliminarse
6. **Revisar logs de auditoría** regularmente
7. **Usar filtros específicos** para operaciones masivas
8. **Verificar permisos** antes de restauraciones
9. **Mantener historial** de reportes generados
10. **Probar en desarrollo** antes de producción

---

## Recursos Adicionales

- Ver ayuda de comandos: `python manage.py <comando> --help`
- Logs del sistema: `/logs/django.log`
- Documentación de modelos: `apps/core/models.py`
- Tests: `tests/test_recycle_bin_management_commands.py`
