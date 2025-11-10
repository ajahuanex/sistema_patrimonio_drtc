# Guía de Validación Manual - Sistema de Papelera de Reciclaje
## Tarea 29: Pruebas Finales de Integración

---

## 🎯 Objetivo

Esta guía proporciona pasos detallados para validar manualmente todos los flujos críticos del sistema de papelera de reciclaje en un ambiente de desarrollo.

---

## ✅ Lista de Verificación de Validación

### Fase 1: Preparación del Ambiente

- [ ] Servidor de desarrollo ejecutándose
- [ ] Base de datos con datos de prueba
- [ ] Usuario administrador creado
- [ ] Usuario regular creado
- [ ] Celery worker ejecutándose (opcional para notificaciones)

#### Comandos de Preparación

```bash
# Iniciar servidor de desarrollo
python manage.py runserver

# Crear superusuario (si no existe)
python manage.py createsuperuser

# Ejecutar migraciones
python manage.py migrate

# Configurar permisos de papelera
python manage.py setup_recycle_permissions

# Configurar papelera inicial
python manage.py setup_recycle_bin
```

---

## 📋 Flujos de Validación

### 1. Soft Delete Universal ✓

#### 1.1 Eliminar una Oficina

**Pasos:**
1. Navegar a `/oficinas/`
2. Seleccionar una oficina existente
3. Hacer clic en "Eliminar"
4. Confirmar eliminación

**Resultado Esperado:**
- ✅ La oficina desaparece de la lista principal
- ✅ Mensaje de confirmación: "Oficina eliminada correctamente"
- ✅ La oficina NO se elimina físicamente de la base de datos

**Verificación en Base de Datos:**
```sql
SELECT id, codigo, nombre, deleted_at, deleted_by_id 
FROM oficinas_oficina 
WHERE deleted_at IS NOT NULL;
```

#### 1.2 Eliminar un Bien Patrimonial

**Pasos:**
1. Navegar a `/bienes/`
2. Seleccionar un bien existente
3. Hacer clic en "Eliminar"
4. Confirmar eliminación

**Resultado Esperado:**
- ✅ El bien desaparece de la lista principal
- ✅ Registro de auditoría creado
- ✅ Entrada en RecycleBin creada

#### 1.3 Eliminar un Catálogo

**Pasos:**
1. Navegar a `/catalogo/`
2. Seleccionar un catálogo sin bienes asociados
3. Hacer clic en "Eliminar"
4. Confirmar eliminación

**Resultado Esperado:**
- ✅ El catálogo desaparece de la lista
- ✅ Validación de dependencias funciona

---

### 2. Papelera de Reciclaje Centralizada ✓

#### 2.1 Acceder a la Papelera

**Pasos:**
1. Hacer clic en el ícono de papelera en el menú principal
2. O navegar directamente a `/recycle-bin/`

**Resultado Esperado:**
- ✅ Vista de papelera se carga correctamente
- ✅ Muestra todos los elementos eliminados
- ✅ Información visible:
  - Tipo de objeto (Oficina, Bien, Catálogo)
  - Nombre/Código del objeto
  - Fecha de eliminación
  - Usuario que eliminó
  - Tiempo restante antes de eliminación automática

#### 2.2 Filtrar Elementos

**Pasos:**
1. En la papelera, usar filtros:
   - Por módulo (Oficinas, Bienes, Catálogo)
   - Por fecha de eliminación
   - Por usuario que eliminó

**Resultado Esperado:**
- ✅ Filtros funcionan correctamente
- ✅ Resultados se actualizan dinámicamente
- ✅ Contador de elementos actualizado

#### 2.3 Buscar en la Papelera

**Pasos:**
1. Usar el campo de búsqueda
2. Ingresar código o nombre de un objeto eliminado

**Resultado Esperado:**
- ✅ Búsqueda funciona
- ✅ Resultados relevantes mostrados

#### 2.4 Vista de Detalle

**Pasos:**
1. Hacer clic en "Ver Detalles" de un elemento
2. Revisar información mostrada

**Resultado Esperado:**
- ✅ Vista previa de datos del objeto
- ✅ Información de eliminación
- ✅ Opciones de restaurar/eliminar permanentemente

---

### 3. Recuperación de Registros ✓

#### 3.1 Restaurar una Oficina

**Pasos:**
1. En la papelera, localizar una oficina eliminada
2. Hacer clic en "Restaurar"
3. Confirmar restauración

**Resultado Esperado:**
- ✅ Oficina restaurada exitosamente
- ✅ Mensaje de confirmación
- ✅ Oficina visible nuevamente en `/oficinas/`
- ✅ Campo `deleted_at` es NULL
- ✅ Campo `restored_at` tiene timestamp
- ✅ Campo `restored_by` tiene el usuario

**Verificación:**
```sql
SELECT id, codigo, nombre, deleted_at, restored_at, restored_by_id 
FROM oficinas_oficina 
WHERE restored_at IS NOT NULL;
```

#### 3.2 Restaurar con Conflicto

**Pasos:**
1. Crear una oficina con código "OF-TEST"
2. Eliminarla
3. Crear otra oficina con el mismo código "OF-TEST"
4. Intentar restaurar la primera

**Resultado Esperado:**
- ✅ Sistema detecta conflicto
- ✅ Mensaje de error claro
- ✅ Opciones para resolver conflicto

#### 3.3 Restauración en Lote

**Pasos:**
1. Seleccionar múltiples elementos (checkbox)
2. Hacer clic en "Restaurar Seleccionados"
3. Confirmar

**Resultado Esperado:**
- ✅ Todos los elementos seleccionados se restauran
- ✅ Mensaje con conteo de restauraciones
- ✅ Elementos desaparecen de la papelera

---

### 4. Eliminación Permanente con Código de Seguridad ✓

#### 4.1 Eliminar Permanentemente un Elemento

**Pasos:**
1. En la papelera, seleccionar un elemento
2. Hacer clic en "Eliminar Permanentemente"
3. Ingresar código de seguridad (ver `.env`: `PERMANENT_DELETE_CODE`)
4. Confirmar

**Resultado Esperado:**
- ✅ Modal solicita código de seguridad
- ✅ Con código correcto: eliminación exitosa
- ✅ Elemento desaparece de la papelera
- ✅ Registro de auditoría creado
- ✅ Snapshot de datos guardado

**Verificación:**
```sql
-- El registro debe estar completamente eliminado
SELECT * FROM oficinas_oficina WHERE id = [ID];

-- Debe existir log de auditoría
SELECT * FROM core_deletionauditlog 
WHERE action = 'permanent_delete' 
ORDER BY timestamp DESC LIMIT 1;
```

#### 4.2 Código de Seguridad Incorrecto

**Pasos:**
1. Intentar eliminar permanentemente
2. Ingresar código incorrecto
3. Intentar 3 veces

**Resultado Esperado:**
- ✅ Primer intento: mensaje de error
- ✅ Segundo intento: advertencia
- ✅ Tercer intento: cuenta bloqueada temporalmente
- ✅ Todos los intentos registrados en logs

#### 4.3 Eliminación Permanente en Lote

**Pasos:**
1. Seleccionar múltiples elementos
2. Hacer clic en "Eliminar Permanentemente Seleccionados"
3. Ingresar código de seguridad
4. Confirmar

**Resultado Esperado:**
- ✅ Solicita código una sola vez
- ✅ Elimina todos los seleccionados
- ✅ Mensaje con conteo

---

### 5. Eliminación Automática por Tiempo ✓

#### 5.1 Verificar Configuración

**Pasos:**
1. Navegar a configuración de papelera
2. Verificar días de retención por módulo

**Resultado Esperado:**
- ✅ Configuración visible
- ✅ Valores por defecto: 30 días

#### 5.2 Ejecutar Limpieza Manual

**Pasos:**
```bash
python manage.py cleanup_recycle_bin --dry-run
```

**Resultado Esperado:**
- ✅ Muestra elementos que serían eliminados
- ✅ No elimina nada (dry-run)

**Ejecución Real:**
```bash
python manage.py cleanup_recycle_bin
```

**Resultado Esperado:**
- ✅ Elimina elementos expirados
- ✅ Muestra conteo de eliminaciones
- ✅ Logs de auditoría creados

#### 5.3 Verificar Tarea Automática de Celery

**Pasos:**
```bash
# Verificar configuración
python verify_celery_tasks.py

# Ver schedule
python manage.py shell
>>> from patrimonio.celery import app
>>> app.conf.beat_schedule
```

**Resultado Esperado:**
- ✅ Tarea `cleanup-recycle-bin` configurada
- ✅ Schedule: diariamente a las 4:00 AM

---

### 6. Sistema de Notificaciones ✓

#### 6.1 Notificación de Advertencia (7 días)

**Pasos:**
1. Crear elemento de prueba con fecha de eliminación en 7 días
2. Ejecutar comando:
```bash
python manage.py shell
>>> from apps.core.tasks import send_recycle_bin_warnings
>>> send_recycle_bin_warnings()
```

**Resultado Esperado:**
- ✅ Email enviado al usuario que eliminó
- ✅ Contenido del email correcto
- ✅ Lista de elementos próximos a eliminarse

#### 6.2 Notificación Final (1 día)

**Pasos:**
1. Crear elemento con fecha de eliminación en 1 día
2. Ejecutar:
```bash
>>> from apps.core.tasks import send_recycle_bin_final_warnings
>>> send_recycle_bin_final_warnings()
```

**Resultado Esperado:**
- ✅ Email de advertencia final enviado
- ✅ Tono urgente en el mensaje

---

### 7. Auditoría y Trazabilidad ✓

#### 7.1 Ver Logs de Auditoría

**Pasos:**
1. Navegar a `/audit/deletion-logs/`
2. Revisar logs de eliminaciones

**Resultado Esperado:**
- ✅ Lista completa de operaciones
- ✅ Información detallada:
  - Acción (soft_delete, restore, permanent_delete)
  - Usuario
  - Timestamp
  - IP address
  - Objeto afectado

#### 7.2 Exportar Reportes

**Pasos:**
1. En vista de auditoría, hacer clic en "Exportar"
2. Seleccionar formato (PDF o Excel)
3. Aplicar filtros si es necesario

**Resultado Esperado:**
- ✅ Archivo descargado
- ✅ Contenido correcto
- ✅ Formato legible

#### 7.3 Ver Snapshot de Datos

**Pasos:**
1. Localizar un log de eliminación permanente
2. Hacer clic en "Ver Detalles"
3. Revisar snapshot

**Resultado Esperado:**
- ✅ Datos completos del objeto antes de eliminación
- ✅ Formato JSON legible

---

### 8. Permisos y Seguridad ✓

#### 8.1 Usuario Regular - Acceso Limitado

**Pasos:**
1. Iniciar sesión como usuario regular (no admin)
2. Navegar a papelera

**Resultado Esperado:**
- ✅ Solo ve elementos que él eliminó
- ✅ No puede ver elementos de otros usuarios
- ✅ No puede eliminar permanentemente

#### 8.2 Usuario Administrador - Acceso Completo

**Pasos:**
1. Iniciar sesión como administrador
2. Navegar a papelera

**Resultado Esperado:**
- ✅ Ve todos los elementos eliminados
- ✅ Puede restaurar cualquier elemento
- ✅ Puede eliminar permanentemente

#### 8.3 Usuario sin Permisos

**Pasos:**
1. Crear usuario sin permisos de papelera
2. Intentar acceder a `/recycle-bin/`

**Resultado Esperado:**
- ✅ Acceso denegado (403)
- ✅ Mensaje claro de falta de permisos

---

### 9. Interfaz de Usuario ✓

#### 9.1 Navegación Principal

**Pasos:**
1. Verificar menú principal
2. Localizar enlace a papelera

**Resultado Esperado:**
- ✅ Ícono de papelera visible
- ✅ Badge con contador de elementos
- ✅ Tooltip informativo

#### 9.2 Accesos Rápidos

**Pasos:**
1. En lista de oficinas, verificar botón de papelera
2. En lista de bienes, verificar botón de papelera

**Resultado Esperado:**
- ✅ Botones de acceso rápido visibles
- ✅ Filtran automáticamente por módulo

#### 9.3 Notificaciones en Tiempo Real

**Pasos:**
1. Tener elementos próximos a eliminarse
2. Verificar widget de notificaciones

**Resultado Esperado:**
- ✅ Widget muestra alertas
- ✅ Contador actualizado
- ✅ Enlaces directos a elementos

---

### 10. Dashboard de Estadísticas ✓

#### 10.1 Ver Dashboard

**Pasos:**
1. Navegar a `/recycle-bin/dashboard/`
2. Revisar estadísticas

**Resultado Esperado:**
- ✅ Gráficos de elementos por módulo
- ✅ Estadísticas de restauraciones vs eliminaciones
- ✅ Tendencias temporales
- ✅ Top usuarios con más eliminaciones

#### 10.2 Exportar Estadísticas

**Pasos:**
1. En dashboard, hacer clic en "Exportar Reporte"
2. Seleccionar rango de fechas

**Resultado Esperado:**
- ✅ Reporte generado
- ✅ Incluye gráficos y tablas

---

## 🔍 Verificaciones de Base de Datos

### Verificar Soft Delete

```sql
-- Contar elementos eliminados por módulo
SELECT 
    'Oficinas' as modulo,
    COUNT(*) as eliminados
FROM oficinas_oficina 
WHERE deleted_at IS NOT NULL

UNION ALL

SELECT 
    'Bienes' as modulo,
    COUNT(*) as eliminados
FROM bienes_bienpatrimonial 
WHERE deleted_at IS NOT NULL

UNION ALL

SELECT 
    'Catálogo' as modulo,
    COUNT(*) as eliminados
FROM catalogo_catalogo 
WHERE deleted_at IS NOT NULL;
```

### Verificar RecycleBin

```sql
-- Ver todos los elementos en papelera
SELECT 
    id,
    module_name,
    object_repr,
    deleted_at,
    auto_delete_at,
    DATEDIFF(auto_delete_at, NOW()) as dias_restantes
FROM core_recyclebin
WHERE restored_at IS NULL
ORDER BY deleted_at DESC;
```

### Verificar Logs de Auditoría

```sql
-- Últimas 10 acciones de auditoría
SELECT 
    action,
    user_id,
    timestamp,
    object_repr,
    ip_address
FROM core_deletionauditlog
ORDER BY timestamp DESC
LIMIT 10;
```

---

## 📊 Métricas de Éxito

### Criterios de Aceptación

| Funcionalidad | Criterio | Estado |
|---------------|----------|--------|
| Soft Delete | Todos los modelos soportan soft delete | ⬜ |
| Papelera Centralizada | Vista funcional con filtros | ⬜ |
| Restauración | Restauración individual y en lote funciona | ⬜ |
| Eliminación Permanente | Código de seguridad requerido y validado | ⬜ |
| Eliminación Automática | Comando funciona correctamente | ⬜ |
| Notificaciones | Emails enviados en tiempos correctos | ⬜ |
| Auditoría | Todos los eventos registrados | ⬜ |
| Permisos | Segregación correcta por rol | ⬜ |
| UI/UX | Interfaz intuitiva y responsive | ⬜ |
| Rendimiento | Operaciones completan en <2 segundos | ⬜ |

---

## 🐛 Registro de Problemas Encontrados

### Formato de Reporte

```markdown
**Problema:** [Descripción breve]
**Severidad:** [Crítico/Alto/Medio/Bajo]
**Pasos para Reproducir:**
1. ...
2. ...

**Resultado Esperado:** ...
**Resultado Actual:** ...
**Screenshots:** [Si aplica]
**Notas Adicionales:** ...
```

---

## ✅ Checklist Final

Antes de considerar la validación completa, verificar:

- [ ] Todos los flujos críticos probados
- [ ] Sin errores críticos encontrados
- [ ] Documentación actualizada
- [ ] Variables de entorno configuradas
- [ ] Migraciones aplicadas
- [ ] Permisos configurados
- [ ] Tareas de Celery funcionando
- [ ] Notificaciones operativas
- [ ] Logs de auditoría completos
- [ ] UI responsive en diferentes dispositivos
- [ ] Rendimiento aceptable

---

## 📝 Notas Finales

### Ambiente de Prueba Recomendado

- **Sistema Operativo:** Windows/Linux/Mac
- **Python:** 3.8+
- **Django:** 4.2+
- **Base de Datos:** PostgreSQL 12+ o SQLite (desarrollo)
- **Navegadores:** Chrome, Firefox, Edge (últimas versiones)

### Datos de Prueba Sugeridos

- 10-20 oficinas
- 50-100 bienes patrimoniales
- 10-15 catálogos
- 3-5 usuarios con diferentes roles

### Tiempo Estimado de Validación

- **Validación Básica:** 1-2 horas
- **Validación Completa:** 3-4 horas
- **Validación con Problemas:** 4-6 horas

---

**Documento creado para:** Tarea 29 - Pruebas Finales de Integración  
**Versión:** 1.0  
**Fecha:** 10 de noviembre de 2025  
**Mantenedor:** Equipo de Desarrollo
