# Task 14: Quick Reference - Eliminación Permanente con Código de Seguridad

## Configuración Rápida

### 1. Ejecutar Migración
```bash
python manage.py migrate
```

### 2. Configurar Código de Seguridad
```bash
# En .env o .env.prod
PERMANENT_DELETE_CODE=TuCodigoSeguro2024!
```

### 3. Verificar Configuración
```bash
python manage.py shell
>>> from django.conf import settings
>>> settings.PERMANENT_DELETE_CODE
```

## Uso Rápido

### Eliminar Elemento Individual

1. Ir a Papelera → Detalle del elemento
2. Click "Eliminar Permanentemente"
3. Ingresar:
   - Código de seguridad
   - Escribir "ELIMINAR"
   - Motivo (mín. 20 caracteres)
4. Confirmar

### Eliminar Múltiples Elementos

1. Papelera → Seleccionar elementos
2. Click "Eliminar Permanentemente"
3. Ingresar código de seguridad
4. Confirmar

## Sistema de Bloqueo

| Intentos Fallidos | Resultado |
|-------------------|-----------|
| 0 | Acceso normal |
| 1 | ⚠️ 2 intentos restantes |
| 2 | ⚠️ 1 intento restante |
| 3 | 🔒 Bloqueado 30 minutos |

## Monitoreo

### Ver Intentos de Código
```
Admin → Core → Security Code Attempts
```

### Ver Auditoría
```
Admin → Core → Audit Logs
Filtrar: action = "delete" o "security_violation"
```

### Consulta SQL Directa
```sql
-- Intentos fallidos recientes
SELECT user_id, COUNT(*) as attempts, MAX(attempted_at) as last_attempt
FROM core_securitycodeattempt
WHERE success = FALSE 
  AND attempted_at > NOW() - INTERVAL '30 minutes'
GROUP BY user_id
HAVING COUNT(*) >= 3;

-- Usuarios bloqueados actualmente
SELECT u.username, COUNT(*) as failed_attempts, 
       MAX(sca.attempted_at) as last_attempt,
       MAX(sca.attempted_at) + INTERVAL '30 minutes' as unlock_time
FROM core_securitycodeattempt sca
JOIN auth_user u ON sca.user_id = u.id
WHERE sca.success = FALSE 
  AND sca.attempted_at > NOW() - INTERVAL '30 minutes'
GROUP BY u.username
HAVING COUNT(*) >= 3;
```

## Troubleshooting

### Usuario Bloqueado

**Problema:** "Usuario bloqueado temporalmente..."

**Soluciones:**
1. Esperar 30 minutos
2. O limpiar intentos (superusuario):
```python
from apps.core.models import SecurityCodeAttempt
from django.contrib.auth.models import User

user = User.objects.get(username='usuario_bloqueado')
SecurityCodeAttempt.objects.filter(user=user, success=False).delete()
```

### Código No Configurado

**Problema:** "Código de seguridad no configurado en el sistema"

**Solución:**
```bash
# Agregar a .env
PERMANENT_DELETE_CODE=TuCodigoSeguro
```

### Código Incorrecto

**Problema:** "Código de seguridad incorrecto"

**Verificar:**
1. Código en .env es correcto
2. No hay espacios extra
3. Es case-sensitive
4. Servidor reiniciado después de cambiar .env

## API de Código

### Verificar Bloqueo
```python
from apps.core.models import SecurityCodeAttempt

is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(user)

if is_locked:
    print(f"Bloqueado. Intentos: {attempts}. Tiempo restante: {time_remaining} min")
```

### Registrar Intento
```python
SecurityCodeAttempt.record_attempt(
    user=user,
    success=False,
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0',
    entry_id=123
)
```

### Obtener Intentos Recientes
```python
recent_failures = SecurityCodeAttempt.get_recent_failed_attempts(user, minutes=30)
print(f"Intentos fallidos: {recent_failures.count()}")
```

## Variables de Configuración

```bash
# Código de seguridad (REQUERIDO)
PERMANENT_DELETE_CODE=TuCodigoSeguro

# Número máximo de intentos antes de bloqueo (default: 3)
RECYCLE_BIN_LOCKOUT_ATTEMPTS=3

# Duración del bloqueo en minutos (default: 30)
RECYCLE_BIN_LOCKOUT_MINUTES=30

# Días de retención en papelera (default: 30)
RECYCLE_BIN_RETENTION_DAYS=30

# Habilitar eliminación automática (default: True)
RECYCLE_BIN_AUTO_CLEANUP_ENABLED=True

# Máximo de elementos en operación en lote (default: 100)
RECYCLE_BIN_MAX_BULK_SIZE=100
```

## Comandos Útiles

### Limpiar Intentos Antiguos
```python
from apps.core.models import SecurityCodeAttempt
from django.utils import timezone
from datetime import timedelta

cutoff = timezone.now() - timedelta(days=30)
SecurityCodeAttempt.objects.filter(attempted_at__lt=cutoff).delete()
```

### Estadísticas de Intentos
```python
from apps.core.models import SecurityCodeAttempt
from django.db.models import Count

stats = SecurityCodeAttempt.objects.values('success').annotate(count=Count('id'))
for stat in stats:
    status = 'Exitosos' if stat['success'] else 'Fallidos'
    print(f"{status}: {stat['count']}")
```

### Usuarios con Más Intentos Fallidos
```python
from apps.core.models import SecurityCodeAttempt
from django.db.models import Count

top_users = (SecurityCodeAttempt.objects
    .filter(success=False)
    .values('user__username')
    .annotate(attempts=Count('id'))
    .order_by('-attempts')[:10])

for user in top_users:
    print(f"{user['user__username']}: {user['attempts']} intentos fallidos")
```

## Mejores Prácticas

### Código de Seguridad

✅ **Hacer:**
- Usar combinación de letras, números y símbolos
- Mínimo 12 caracteres
- Cambiar periódicamente (cada 3-6 meses)
- Almacenar en gestor de contraseñas
- Compartir solo con administradores autorizados

❌ **No hacer:**
- Usar palabras comunes
- Compartir por email/chat sin cifrar
- Reutilizar de otros sistemas
- Escribir en lugares visibles

### Monitoreo

✅ **Revisar regularmente:**
- Intentos fallidos múltiples del mismo usuario
- Intentos desde IPs sospechosas
- Patrones de intentos (horarios inusuales)
- Usuarios bloqueados frecuentemente

### Respuesta a Incidentes

Si detecta actividad sospechosa:

1. **Cambiar código inmediatamente**
2. **Revisar logs de auditoría**
3. **Verificar IPs de intentos**
4. **Contactar usuarios afectados**
5. **Documentar incidente**

## Ejemplos de Código

### Eliminar Permanentemente (Programático)
```python
from apps.core.utils import RecycleBinService
from apps.core.models import RecycleBin

entry = RecycleBin.objects.get(id=123)
user = request.user
code = 'TuCodigoSeguro'

success, message = RecycleBinService.permanent_delete(
    entry,
    user,
    code,
    reason='Eliminación por política de retención',
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT')
)

if success:
    print("Eliminado exitosamente")
else:
    print(f"Error: {message}")
```

### Verificar Estado de Usuario
```python
from apps.core.models import SecurityCodeAttempt

def check_user_status(user):
    is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(user)
    
    if is_locked:
        return f"🔒 Bloqueado ({time_remaining} min restantes)"
    elif attempts > 0:
        remaining = 3 - attempts
        return f"⚠️ {attempts} intentos fallidos ({remaining} restantes)"
    else:
        return "✅ Sin restricciones"

print(check_user_status(user))
```

## Testing

### Test Manual Rápido

1. **Intento exitoso:**
```bash
# Usar código correcto
# Verificar eliminación
# Verificar registro en SecurityCodeAttempt (success=True)
```

2. **Intento fallido:**
```bash
# Usar código incorrecto
# Verificar mensaje de error
# Verificar registro en SecurityCodeAttempt (success=False)
```

3. **Bloqueo:**
```bash
# Hacer 3 intentos fallidos
# Verificar mensaje de bloqueo
# Intentar con código correcto (debe fallar)
# Esperar 30 minutos o limpiar intentos
```

### Test Automatizado
```bash
python manage.py test tests.test_security_code_attempt -v 2
```

## Soporte

### Logs a Revisar

1. **Django logs:**
```bash
tail -f logs/django.log | grep -i "security\|permanent"
```

2. **Base de datos:**
```sql
-- Últimos 10 intentos
SELECT * FROM core_securitycodeattempt 
ORDER BY attempted_at DESC LIMIT 10;

-- Auditoría de eliminaciones permanentes
SELECT * FROM core_auditlog 
WHERE action = 'delete' 
  AND changes::text LIKE '%permanent_delete%'
ORDER BY timestamp DESC LIMIT 10;
```

### Contacto

Para problemas con el sistema de eliminación permanente:
1. Revisar esta guía
2. Consultar logs
3. Verificar configuración
4. Contactar equipo de desarrollo

## Changelog

### v1.0 (Task 14)
- ✅ Modelo SecurityCodeAttempt
- ✅ Sistema de bloqueo temporal
- ✅ Validación de código de seguridad
- ✅ Logging completo
- ✅ Template con advertencias
- ✅ Tests completos
