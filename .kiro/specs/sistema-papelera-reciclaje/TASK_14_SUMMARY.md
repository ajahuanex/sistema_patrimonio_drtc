# Task 14: Implementación de Eliminación Permanente con Código de Seguridad

## ✅ Completado

Se ha implementado exitosamente el sistema de eliminación permanente con código de seguridad, incluyendo validación, logging y bloqueo temporal tras intentos fallidos.

## Componentes Implementados

### 1. Modelo SecurityCodeAttempt

**Ubicación:** `apps/core/models.py`

Nuevo modelo para registrar todos los intentos de uso del código de seguridad:

```python
class SecurityCodeAttempt(models.Model):
    user = ForeignKey(User)
    attempted_at = DateTimeField(auto_now_add=True)
    success = BooleanField(default=False)
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    recycle_bin_entry_id = PositiveIntegerField()
```

**Características:**
- Registro automático de todos los intentos (exitosos y fallidos)
- Almacena IP y User Agent para auditoría
- Índices optimizados para consultas frecuentes
- Métodos de clase para verificar bloqueos

**Métodos principales:**
- `get_recent_failed_attempts(user, minutes=30)`: Obtiene intentos fallidos recientes
- `is_user_locked_out(user, max_attempts=3, lockout_minutes=30)`: Verifica si usuario está bloqueado
- `record_attempt(user, success, ...)`: Registra un intento

### 2. RecycleBinService Mejorado

**Ubicación:** `apps/core/utils.py`

Método `permanent_delete()` actualizado con:

```python
def permanent_delete(recycle_entry, user, security_code, reason='', 
                    ip_address=None, user_agent=None):
    # 1. Verificar permisos de administrador
    # 2. Verificar bloqueo temporal
    # 3. Validar código de seguridad
    # 4. Registrar intento (exitoso o fallido)
    # 5. Eliminar permanentemente si código es correcto
    # 6. Registrar en auditoría completa
```

**Mejoras implementadas:**
- ✅ Validación contra variable `PERMANENT_DELETE_CODE`
- ✅ Sistema de bloqueo temporal (3 intentos / 30 minutos)
- ✅ Logging detallado de todos los intentos
- ✅ Mensajes informativos sobre intentos restantes
- ✅ Registro de IP y User Agent
- ✅ Auditoría completa en AuditLog

### 3. Vista PermanentDeleteView

**Ubicación:** `apps/core/views.py`

Vista `recycle_bin_permanent_delete()` mejorada:

**Características:**
- Verificación de bloqueo antes de mostrar formulario
- Captura de IP y User Agent del request
- Manejo de errores con mensajes descriptivos
- Contador de intentos restantes
- Redirección inteligente según tipo de error

**Contexto del template:**
```python
context = {
    'entry': entry,
    'form': form,
    'attempts_count': attempts_count,
    'remaining_attempts': remaining_attempts,
    'show_warning': attempts_count > 0,
}
```

### 4. Formulario PermanentDeleteForm Mejorado

**Ubicación:** `apps/core/forms.py`

**Mejoras:**
- Verificación de bloqueo en `__init__`
- Deshabilita campos si usuario está bloqueado
- Validación de bloqueo en `clean()`
- Mensajes de ayuda dinámicos

**Campos:**
- `security_code`: Código de seguridad (PasswordInput)
- `confirm_text`: Confirmación "ELIMINAR"
- `reason`: Motivo detallado (mínimo 20 caracteres)

### 5. Template de Eliminación Permanente

**Ubicación:** `templates/core/recycle_bin_permanent_delete_form.html`

**Características:**
- Advertencias visuales prominentes
- Contador de intentos restantes
- Información de seguridad clara
- Validación JavaScript en tiempo real
- Confirmación final antes de envío
- Contador de caracteres para motivo
- Diseño responsive

**Secciones:**
1. Advertencia de peligro (rojo)
2. Advertencia de bloqueo (si aplica)
3. Información del elemento
4. Requisitos de seguridad
5. Formulario con validaciones
6. Nota de auditoría

### 6. Configuración de Variables de Entorno

**Archivos actualizados:**
- `.env`
- `.env.local`
- `.env.prod.example`
- `patrimonio/settings.py`

**Variables agregadas:**
```bash
PERMANENT_DELETE_CODE=CHANGE-THIS-IN-PRODUCTION
RECYCLE_BIN_RETENTION_DAYS=30
RECYCLE_BIN_AUTO_CLEANUP_ENABLED=True
RECYCLE_BIN_MAX_BULK_SIZE=100
RECYCLE_BIN_LOCKOUT_ATTEMPTS=3
RECYCLE_BIN_LOCKOUT_MINUTES=30
```

### 7. Admin Interface

**Ubicación:** `apps/core/admin.py`

Nuevo admin para `SecurityCodeAttempt`:
- Lista de intentos con estado visual (✓/✗)
- Filtros por éxito y fecha
- Solo lectura (no se pueden modificar)
- Solo superusuarios pueden eliminar

### 8. Migración de Base de Datos

**Archivo:** `apps/core/migrations/0003_add_security_code_attempt_model.py`

Crea tabla `core_securitycodeattempt` con:
- Campos del modelo
- Índices optimizados
- Constraints de integridad

### 9. Tests Completos

**Ubicación:** `tests/test_security_code_attempt.py`

**Cobertura de tests:**

#### SecurityCodeAttemptModelTest (11 tests)
- ✅ Crear registro de intento
- ✅ Método record_attempt
- ✅ Obtener intentos fallidos recientes
- ✅ Ventana de tiempo para intentos
- ✅ Usuario sin intentos no bloqueado
- ✅ Usuario con intentos bajo umbral
- ✅ Usuario bloqueado al alcanzar umbral
- ✅ Bloqueo expira después del tiempo
- ✅ Intentos exitosos no cuentan para bloqueo
- ✅ Bloqueos independientes por usuario
- ✅ Representación en string

#### SecurityCodeIntegrationTest (4 tests)
- ✅ Eliminación con código correcto
- ✅ Eliminación con código incorrecto
- ✅ Bloqueo después de múltiples fallos
- ✅ Mensaje muestra intentos restantes

## Flujo de Funcionamiento

### Eliminación Permanente Individual

```
1. Usuario accede a detalle de elemento en papelera
2. Click en "Eliminar Permanentemente"
3. Sistema verifica:
   - ¿Es administrador? → No: Error
   - ¿Está bloqueado? → Sí: Mostrar tiempo restante
4. Muestra formulario con:
   - Advertencias de peligro
   - Contador de intentos (si hay fallos previos)
   - Campos de seguridad
5. Usuario completa formulario
6. Sistema valida:
   - Código de seguridad
   - Texto de confirmación "ELIMINAR"
   - Motivo (mínimo 20 caracteres)
7. Si código incorrecto:
   - Registra intento fallido
   - Muestra intentos restantes
   - Si alcanza 3 intentos: Bloquea 30 minutos
8. Si código correcto:
   - Registra intento exitoso
   - Elimina permanentemente
   - Registra en auditoría
   - Redirige a lista
```

### Sistema de Bloqueo

```
Intentos Fallidos → Acción
─────────────────────────────
0 intentos       → Acceso normal
1 intento        → Advertencia: 2 intentos restantes
2 intentos       → Advertencia: 1 intento restante
3 intentos       → BLOQUEADO por 30 minutos
Después de 30min → Bloqueo se levanta automáticamente
```

## Seguridad Implementada

### 1. Validación de Código
- Código almacenado en variable de entorno
- Comparación exacta (case-sensitive)
- No se expone en logs ni mensajes de error

### 2. Sistema de Bloqueo Temporal
- 3 intentos fallidos máximo
- Bloqueo de 30 minutos
- Contador independiente por usuario
- Ventana deslizante de tiempo

### 3. Auditoría Completa
- Registro en `SecurityCodeAttempt`
- Registro en `AuditLog`
- Captura de IP y User Agent
- Timestamp preciso
- Datos del objeto eliminado

### 4. Permisos Estrictos
- Solo administradores pueden eliminar permanentemente
- Verificación en múltiples capas:
  - Vista
  - Formulario
  - Servicio

### 5. Confirmaciones Múltiples
- Código de seguridad
- Texto "ELIMINAR"
- Motivo detallado
- Confirmación JavaScript final

## Configuración Requerida

### Producción

1. **Configurar código de seguridad seguro:**
```bash
# .env.prod
PERMANENT_DELETE_CODE=TuCodigoSuperSeguro2024!
```

2. **Ajustar parámetros de bloqueo (opcional):**
```bash
RECYCLE_BIN_LOCKOUT_ATTEMPTS=5
RECYCLE_BIN_LOCKOUT_MINUTES=60
```

3. **Ejecutar migración:**
```bash
python manage.py migrate
```

4. **Verificar configuración:**
```bash
python manage.py shell
>>> from django.conf import settings
>>> settings.PERMANENT_DELETE_CODE
'TuCodigoSuperSeguro2024!'
```

### Desarrollo

Código ya configurado en `.env`:
```bash
PERMANENT_DELETE_CODE=DEV-DELETE-CODE-123
```

## Uso

### Para Administradores

1. **Eliminar elemento individual:**
   - Ir a Papelera de Reciclaje
   - Click en elemento
   - Click "Eliminar Permanentemente"
   - Ingresar código de seguridad
   - Escribir "ELIMINAR"
   - Proporcionar motivo
   - Confirmar

2. **Eliminar múltiples elementos:**
   - Seleccionar elementos en lista
   - Click "Eliminar Permanentemente"
   - Ingresar código de seguridad
   - Confirmar operación en lote

3. **Si se bloquea:**
   - Esperar 30 minutos
   - O contactar a superusuario para limpiar intentos

### Monitoreo

**Ver intentos de código:**
```
Admin → Core → Security Code Attempts
```

**Ver auditoría:**
```
Admin → Core → Audit Logs
Filtrar por: action = "delete" o "security_violation"
```

## Mensajes del Sistema

### Código Correcto
```
"Objeto eliminado permanentemente"
```

### Código Incorrecto (1er intento)
```
"Código de seguridad incorrecto. Le quedan 2 intento(s) antes del bloqueo temporal."
```

### Código Incorrecto (3er intento)
```
"Código de seguridad incorrecto. Usuario bloqueado temporalmente por 30 minutos."
```

### Usuario Bloqueado
```
"Usuario bloqueado temporalmente por múltiples intentos fallidos. Intente nuevamente en 25 minutos."
```

## Archivos Modificados/Creados

### Modelos
- ✅ `apps/core/models.py` - Agregado SecurityCodeAttempt

### Vistas
- ✅ `apps/core/views.py` - Mejorado recycle_bin_permanent_delete
- ✅ `apps/core/views.py` - Mejorado recycle_bin_bulk_permanent_delete

### Servicios
- ✅ `apps/core/utils.py` - Mejorado RecycleBinService.permanent_delete

### Formularios
- ✅ `apps/core/forms.py` - Mejorado PermanentDeleteForm
- ✅ `apps/core/forms.py` - Mejorado BulkOperationForm

### Templates
- ✅ `templates/core/recycle_bin_permanent_delete_form.html` - Nuevo

### Admin
- ✅ `apps/core/admin.py` - Agregado SecurityCodeAttemptAdmin

### Configuración
- ✅ `patrimonio/settings.py` - Agregadas variables de configuración
- ✅ `.env` - Agregadas variables
- ✅ `.env.local` - Agregadas variables
- ✅ `.env.prod.example` - Agregadas variables

### Migraciones
- ✅ `apps/core/migrations/0003_add_security_code_attempt_model.py`

### Tests
- ✅ `tests/test_security_code_attempt.py` - 15 tests completos

## Verificación

### Checklist de Implementación

- [x] Modelo SecurityCodeAttempt creado
- [x] Métodos de verificación de bloqueo implementados
- [x] RecycleBinService.permanent_delete mejorado
- [x] Vista PermanentDeleteView con verificación de bloqueo
- [x] Formulario con validación de bloqueo
- [x] Template con advertencias y contador
- [x] Variables de entorno configuradas
- [x] Admin interface para SecurityCodeAttempt
- [x] Migración de base de datos
- [x] Tests completos (15 tests)
- [x] Logging de intentos en SecurityCodeAttempt
- [x] Logging de intentos en AuditLog
- [x] Captura de IP y User Agent
- [x] Sistema de bloqueo temporal funcional
- [x] Mensajes informativos de intentos restantes
- [x] Documentación completa

## Próximos Pasos

Para completar la integración:

1. **Ejecutar migración en producción:**
```bash
python manage.py migrate
```

2. **Configurar código de seguridad seguro**

3. **Probar flujo completo:**
   - Intento exitoso
   - Intentos fallidos
   - Bloqueo temporal
   - Desbloqueo automático

4. **Capacitar administradores:**
   - Uso del código de seguridad
   - Qué hacer si se bloquean
   - Cómo monitorear intentos

5. **Monitorear logs:**
   - Revisar SecurityCodeAttempt regularmente
   - Detectar patrones sospechosos
   - Ajustar parámetros si es necesario

## Notas de Seguridad

⚠️ **IMPORTANTE:**

1. **Código de Seguridad:**
   - Cambiar en producción
   - No compartir públicamente
   - Rotar periódicamente
   - Usar combinación de letras, números y símbolos

2. **Monitoreo:**
   - Revisar intentos fallidos regularmente
   - Investigar múltiples intentos del mismo usuario
   - Alertar sobre patrones sospechosos

3. **Backup:**
   - Siempre hacer backup antes de eliminación permanente
   - Considerar período de retención más largo
   - Documentar razones de eliminación

## Cumplimiento de Requisitos

### Requirement 4.1 ✅
> WHEN intento eliminar permanentemente un registro THEN el sistema SHALL solicitar un código de seguridad especial

**Implementado:** Formulario solicita código de seguridad en campo password

### Requirement 4.2 ✅
> WHEN ingreso el código de seguridad THEN el sistema SHALL validarlo contra una variable de entorno (PERMANENT_DELETE_CODE)

**Implementado:** Validación en RecycleBinService.permanent_delete() contra settings.PERMANENT_DELETE_CODE

### Requirement 4.3 ✅
> IF el código es incorrecto THEN el sistema SHALL denegar la operación y registrar el intento

**Implementado:** 
- Registro en SecurityCodeAttempt
- Registro en AuditLog
- Mensaje de error al usuario

### Requirement 8.4 ✅
> Sistema de protección contra ataques de seguridad

**Implementado:**
- Bloqueo temporal tras 3 intentos fallidos
- Ventana deslizante de 30 minutos
- Logging completo de intentos
- Captura de IP y User Agent

## Conclusión

✅ **Task 14 completada exitosamente**

Se ha implementado un sistema robusto de eliminación permanente con:
- Validación de código de seguridad
- Sistema de bloqueo temporal
- Logging completo de intentos
- Auditoría detallada
- Interfaz de usuario clara
- Tests completos

El sistema está listo para uso en producción una vez configurado el código de seguridad.
