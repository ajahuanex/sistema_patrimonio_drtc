# Task 18: Comandos de Management - Guía Rápida

## 🚀 Comandos Disponibles

### 1. restore_from_backup - Restauración de Emergencia

#### Listar elementos disponibles
```bash
python manage.py restore_from_backup --list-only
```

#### Restaurar elemento específico
```bash
python manage.py restore_from_backup --audit-log-id=123 --force
```

#### Filtrar por fecha
```bash
python manage.py restore_from_backup \
  --date-from=2025-01-01 \
  --date-to=2025-01-31 \
  --list-only
```

#### Filtrar por módulo y usuario
```bash
python manage.py restore_from_backup \
  --module=oficinas \
  --user=admin \
  --list-only
```

#### Restaurar con recreación de entrada
```bash
python manage.py restore_from_backup \
  --audit-log-id=456 \
  --force \
  --recreate-recycle-entry
```

---

### 2. generate_recycle_report - Reportes de Auditoría

#### Reporte básico en texto
```bash
python manage.py generate_recycle_report --format=txt
```

#### Reporte JSON con salida a archivo
```bash
python manage.py generate_recycle_report \
  --format=json \
  --output=reporte_papelera.json
```

#### Reporte CSV
```bash
python manage.py generate_recycle_report \
  --format=csv \
  --output=reporte.csv
```

#### Solo estadísticas
```bash
python manage.py generate_recycle_report --statistics-only
```

#### Reporte con logs de auditoría
```bash
python manage.py generate_recycle_report \
  --audit-logs \
  --format=json \
  --output=reporte_completo.json
```

#### Reporte por período
```bash
python manage.py generate_recycle_report \
  --date-from=2025-01-01 \
  --date-to=2025-01-31 \
  --format=csv \
  --output=enero_2025.csv
```

#### Reporte por módulo
```bash
python manage.py generate_recycle_report \
  --module=oficinas \
  --format=txt
```

#### Incluir elementos restaurados
```bash
python manage.py generate_recycle_report \
  --include-restored \
  --format=json
```

---

### 3. update_retention_policies - Actualización de Políticas

#### Ver configuraciones actuales
```bash
python manage.py update_retention_policies --show-current
```

#### Ver configuración de un módulo
```bash
python manage.py update_retention_policies \
  --module=oficinas \
  --show-current
```

#### Actualizar días de retención
```bash
python manage.py update_retention_policies \
  --module=oficinas \
  --retention-days=60 \
  --force
```

#### Actualizar todos los módulos
```bash
python manage.py update_retention_policies \
  --module=all \
  --retention-days=45 \
  --force
```

#### Actualizar días de advertencia
```bash
python manage.py update_retention_policies \
  --module=bienes \
  --warning-days=14 \
  --final-warning-days=3 \
  --force
```

#### Habilitar eliminación automática
```bash
python manage.py update_retention_policies \
  --module=catalogo \
  --enable-auto-delete \
  --force
```

#### Deshabilitar eliminación automática
```bash
python manage.py update_retention_policies \
  --module=all \
  --disable-auto-delete \
  --force
```

#### Actualizar permisos de restauración
```bash
python manage.py update_retention_policies \
  --module=oficinas \
  --enable-restore-others \
  --force
```

#### Actualizar elementos existentes
```bash
python manage.py update_retention_policies \
  --module=bienes \
  --retention-days=90 \
  --update-existing-items \
  --force
```

#### Dry-run (previsualizar cambios)
```bash
python manage.py update_retention_policies \
  --module=all \
  --retention-days=120 \
  --dry-run
```

#### Actualización completa
```bash
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --warning-days=14 \
  --final-warning-days=3 \
  --enable-auto-delete \
  --enable-restore-own \
  --update-existing-items \
  --force
```

---

## 📋 Opciones Comunes

### restore_from_backup
| Opción | Descripción |
|--------|-------------|
| `--audit-log-id` | ID del log de auditoría a restaurar |
| `--date-from` | Fecha desde (YYYY-MM-DD) |
| `--date-to` | Fecha hasta (YYYY-MM-DD) |
| `--module` | Módulo (oficinas, bienes, catalogo, core) |
| `--user` | Usuario que eliminó |
| `--list-only` | Solo listar sin restaurar |
| `--force` | Forzar restauración |
| `--recreate-recycle-entry` | Recrear entrada en RecycleBin |

### generate_recycle_report
| Opción | Descripción |
|--------|-------------|
| `--format` | Formato (json, csv, txt) |
| `--output` | Archivo de salida |
| `--date-from` | Fecha desde (YYYY-MM-DD) |
| `--date-to` | Fecha hasta (YYYY-MM-DD) |
| `--module` | Módulo específico |
| `--user` | Usuario que eliminó |
| `--include-restored` | Incluir restaurados |
| `--include-deleted` | Incluir eliminados permanentemente |
| `--statistics-only` | Solo estadísticas |
| `--audit-logs` | Incluir logs de auditoría |

### update_retention_policies
| Opción | Descripción |
|--------|-------------|
| `--module` | Módulo (oficinas, bienes, catalogo, core, all) |
| `--retention-days` | Días de retención |
| `--warning-days` | Días de advertencia |
| `--final-warning-days` | Días de advertencia final |
| `--enable-auto-delete` | Habilitar auto-delete |
| `--disable-auto-delete` | Deshabilitar auto-delete |
| `--enable-restore-own` | Habilitar restaurar propios |
| `--disable-restore-own` | Deshabilitar restaurar propios |
| `--enable-restore-others` | Habilitar restaurar de otros |
| `--disable-restore-others` | Deshabilitar restaurar de otros |
| `--update-existing-items` | Actualizar elementos existentes |
| `--dry-run` | Previsualizar sin aplicar |
| `--force` | Forzar sin confirmación |
| `--show-current` | Mostrar configuraciones actuales |

---

## 🎯 Casos de Uso Comunes

### Recuperación de Emergencia
```bash
# 1. Buscar elemento eliminado
python manage.py restore_from_backup --date-from=2025-01-09 --list-only

# 2. Restaurar elemento
python manage.py restore_from_backup --audit-log-id=789 --force
```

### Auditoría Mensual
```bash
# Generar reporte del mes
python manage.py generate_recycle_report \
  --date-from=2025-01-01 \
  --date-to=2025-01-31 \
  --format=csv \
  --output=reporte_enero.csv \
  --audit-logs
```

### Cambio de Política Global
```bash
# 1. Ver configuración actual
python manage.py update_retention_policies --show-current

# 2. Previsualizar cambios
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --dry-run

# 3. Aplicar cambios
python manage.py update_retention_policies \
  --module=all \
  --retention-days=90 \
  --update-existing-items \
  --force
```

### Mantenimiento Programado
```bash
# Deshabilitar auto-delete temporalmente
python manage.py update_retention_policies \
  --module=all \
  --disable-auto-delete \
  --force

# Generar reporte antes de mantenimiento
python manage.py generate_recycle_report \
  --format=json \
  --output=backup_pre_mantenimiento.json

# Restaurar auto-delete después
python manage.py update_retention_policies \
  --module=all \
  --enable-auto-delete \
  --force
```

---

## ⚠️ Notas Importantes

1. **--force**: Siempre requerido para aplicar cambios (excepto en --list-only y --show-current)
2. **--dry-run**: Útil para previsualizar cambios antes de aplicarlos
3. **Fechas**: Usar formato YYYY-MM-DD
4. **Módulos**: Valores válidos: oficinas, bienes, catalogo, core, all
5. **Formatos**: json, csv, txt
6. **Auditoría**: Todos los cambios se registran en AuditLog

---

## 🔍 Ayuda Adicional

Para ver todas las opciones de un comando:
```bash
python manage.py <comando> --help
```

Ejemplos:
```bash
python manage.py restore_from_backup --help
python manage.py generate_recycle_report --help
python manage.py update_retention_policies --help
```
