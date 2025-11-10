# Task 22: Reportes de Auditoría - Guía Rápida

## 🚀 Acceso Rápido

### URLs Principales
```
Reportes:     /core/auditoria/eliminaciones/
Exportar:     /core/auditoria/eliminaciones/exportar/?format=excel
Detalle:      /core/auditoria/eliminaciones/<log_id>/
```

## 📊 Filtros Disponibles

| Filtro | Tipo | Descripción |
|--------|------|-------------|
| `user` | texto | Nombre de usuario |
| `action` | select | Tipo de acción (soft_delete, restore, etc.) |
| `module` | texto | Módulo (oficinas, bienes, catálogo) |
| `success` | select | Estado (true/false) |
| `date_from` | fecha | Fecha desde (YYYY-MM-DD) |
| `date_to` | fecha | Fecha hasta (YYYY-MM-DD) |
| `search` | texto | Búsqueda en objeto, motivo, error |

### Ejemplo de URL con Filtros
```
/core/auditoria/eliminaciones/?user=admin&action=permanent_delete&date_from=2025-01-01
```

## 🎯 Patrones Sospechosos

### 1. Múltiples Eliminaciones Permanentes ⚠️
- **Severidad:** Alta
- **Umbral:** 5+ en 1 hora
- **Acción:** Revisar inmediatamente

### 2. Múltiples Intentos Fallidos ⚡
- **Severidad:** Media
- **Umbral:** 3+ en 1 hora
- **Acción:** Verificar permisos

### 3. Eliminaciones Masivas 🔥
- **Severidad:** Alta
- **Umbral:** 20+ en 24 horas
- **Acción:** Confirmar intención

### 4. Actividad Fuera de Horario 🌙
- **Severidad:** Baja
- **Umbral:** 5+ operaciones (10pm-6am)
- **Acción:** Monitorear

### 5. Restaurar y Eliminar 🔄
- **Severidad:** Media
- **Umbral:** 3+ de cada tipo
- **Acción:** Investigar motivo

## 📥 Exportación

### Excel
```bash
# Exportar todos los logs
GET /core/auditoria/eliminaciones/exportar/?format=excel

# Exportar con filtros
GET /core/auditoria/eliminaciones/exportar/?format=excel&user=admin&date_from=2025-01-01
```

**Características:**
- Hoja de datos completa
- Hoja de estadísticas
- Formato profesional
- Límite: 10,000 registros

### PDF
```bash
# Exportar a PDF
GET /core/auditoria/eliminaciones/exportar/?format=pdf

# Con filtros
GET /core/auditoria/eliminaciones/exportar/?format=pdf&action=permanent_delete
```

**Características:**
- Orientación horizontal
- Estadísticas incluidas
- Primeras 100 operaciones
- Formato profesional

## 🔔 Alertas Automáticas

### Comando Manual
```bash
# Analizar últimas 24 horas
python manage.py check_suspicious_patterns

# Analizar últimas 48 horas
python manage.py check_suspicious_patterns --hours 48

# Enviar notificaciones
python manage.py check_suspicious_patterns --send-notifications

# Modo verbose
python manage.py check_suspicious_patterns --verbose --send-notifications
```

### Configuración Automática (Crontab)
```bash
# Cada hora
0 * * * * cd /path/to/project && python manage.py check_suspicious_patterns --send-notifications

# Cada 6 horas
0 */6 * * * cd /path/to/project && python manage.py check_suspicious_patterns --send-notifications

# Diario a las 8am
0 8 * * * cd /path/to/project && python manage.py check_suspicious_patterns --hours 24 --send-notifications
```

## 📊 Estadísticas Disponibles

### Generales
- Total de operaciones
- Operaciones exitosas
- Operaciones fallidas

### Por Acción
- soft_delete
- restore
- permanent_delete
- auto_delete
- bulk_restore
- bulk_delete
- failed_restore
- failed_delete

### Por Módulo
- oficinas
- bienes
- catalogo
- core

### Por Usuario
- Top 10 usuarios más activos
- Conteo de operaciones por usuario

### Tendencias
- Últimos 30 días
- Desglose por acción
- Gráfico interactivo

## 🔒 Permisos Requeridos

| Vista | Permiso | Roles |
|-------|---------|-------|
| Reportes | `can_view_deletion_audit_logs` | Administrador, Auditor |
| Exportar | `can_view_deletion_audit_logs` | Administrador, Auditor |
| Detalle | `can_view_deletion_audit_logs` | Administrador, Auditor |

## 🎨 Elementos de UI

### Badges de Acción
- 🟡 Eliminación Lógica (amarillo)
- 🟢 Restauración (verde)
- 🔴 Eliminación Permanente (rojo)
- ⚫ Eliminación Automática (gris)
- 🔵 Restauración en Lote (azul)
- 🟠 Eliminación en Lote (naranja)

### Badges de Estado
- ✓ Exitoso (verde)
- ✗ Fallido (rojo)

### Alertas de Patrones
- 🔴 Alta Severidad (rojo)
- 🟡 Media Severidad (amarillo)
- 🟢 Baja Severidad (azul)

## 📱 Responsive Design

El sistema es completamente responsive:
- Desktop: Vista completa con todas las columnas
- Tablet: Columnas ajustadas
- Mobile: Vista optimizada con scroll horizontal

## 🔧 Personalización

### Cambiar Umbrales de Patrones
Editar en `apps/core/views.py` función `_detect_suspicious_patterns()`:

```python
# Línea ~XXX
permanent_deletes_threshold = 5  # Cambiar aquí
failures_threshold = 3
massive_deletes_threshold = 20
```

### Agregar Columnas a Exportación
Editar en `apps/core/views.py` funciones:
- `_export_to_excel()` - línea ~XXX
- `_export_to_pdf()` - línea ~XXX

### Personalizar Gráficos
Editar en `templates/core/deletion_audit_reports.html`:
- Configuración de Chart.js (línea ~XXX)
- Colores de series
- Tipo de gráfico

## 🐛 Troubleshooting

### Error: "openpyxl no está instalada"
```bash
pip install openpyxl
```

### Error: "reportlab no está instalada"
```bash
pip install reportlab
```

### No se muestran patrones sospechosos
- Verificar que hay suficientes logs en el período
- Revisar umbrales de detección
- Verificar que los logs tienen timestamps correctos

### Exportación muy lenta
- Reducir rango de fechas
- Aplicar más filtros
- El límite es 10,000 registros

### Gráfico no se muestra
- Verificar que Chart.js está cargado
- Revisar consola del navegador
- Verificar que hay datos en el período

## 📚 Recursos Adicionales

### Documentación Completa
- Ver: `TASK_22_IMPLEMENTATION_SUMMARY.md`

### Tests
- Archivo: `tests/test_deletion_audit_reports.py`
- Ejecutar: `python manage.py test tests.test_deletion_audit_reports`

### Código Fuente
- Vistas: `apps/core/views.py`
- URLs: `apps/core/urls.py`
- Templates: `templates/core/deletion_audit_*.html`
- Comando: `apps/core/management/commands/check_suspicious_patterns.py`

## 💡 Tips y Mejores Prácticas

1. **Exportar regularmente** los reportes para mantener histórico
2. **Configurar alertas automáticas** para detección temprana
3. **Revisar patrones sospechosos** al menos una vez al día
4. **Usar filtros** para análisis específicos
5. **Documentar** acciones tomadas en respuesta a alertas
6. **Capacitar** a auditores en el uso del sistema
7. **Revisar umbrales** periódicamente según el uso del sistema

## 🎯 Casos de Uso Comunes

### 1. Auditoría Mensual
```
1. Ir a reportes
2. Filtrar por mes anterior (date_from, date_to)
3. Exportar a PDF
4. Revisar estadísticas
5. Archivar reporte
```

### 2. Investigar Usuario Específico
```
1. Filtrar por usuario
2. Revisar todas sus operaciones
3. Ver detalles de operaciones sospechosas
4. Exportar evidencia si es necesario
```

### 3. Análisis de Seguridad
```
1. Revisar patrones sospechosos
2. Filtrar por eliminaciones permanentes
3. Verificar uso de código de seguridad
4. Revisar actividad fuera de horario
```

### 4. Reporte para Dirección
```
1. Filtrar por período (trimestre/año)
2. Exportar a PDF
3. Incluir estadísticas generales
4. Destacar patrones detectados
```

## ✅ Checklist de Verificación

- [ ] Acceso a reportes funciona
- [ ] Filtros aplican correctamente
- [ ] Exportación a Excel funciona
- [ ] Exportación a PDF funciona
- [ ] Gráficos se muestran correctamente
- [ ] Patrones sospechosos se detectan
- [ ] Alertas automáticas configuradas
- [ ] Permisos correctamente asignados
- [ ] Tests pasan exitosamente
- [ ] Documentación revisada

## 📞 Soporte

Para problemas o preguntas:
1. Revisar esta guía
2. Consultar documentación completa
3. Revisar logs del sistema
4. Contactar al equipo de desarrollo
