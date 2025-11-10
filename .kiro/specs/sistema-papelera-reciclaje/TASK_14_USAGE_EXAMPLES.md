# Task 14: Usage Examples - Eliminación Permanente con Código de Seguridad

## Ejemplos Prácticos de Uso

### Ejemplo 1: Eliminación Permanente Individual Exitosa

**Escenario:** Administrador necesita eliminar permanentemente una oficina que ya no existe.

**Pasos:**

1. **Navegar a la papelera:**
```
Dashboard → Papelera de Reciclaje
```

2. **Buscar el elemento:**
```
Filtrar por: Módulo = "Oficinas"
Buscar: "Oficina Cerrada 2023"
```

3. **Ver detalles:**
```
Click en "Oficina Cerrada 2023"
Revisar información:
- Eliminado por: Juan Pérez
- Fecha: 15/01/2024
- Motivo: Oficina cerrada por reestructuración
```

4. **Iniciar eliminación permanente:**
```
Click en botón "Eliminar Permanentemente"
```

5. **Completar formulario:**
```
Código de Seguridad: [Ingresar código configurado]
Confirmar: ELIMINAR
Motivo: "Oficina cerrada definitivamente. Ya no existe físicamente 
         y no hay posibilidad de restauración. Eliminación aprobada 
         por Dirección General según memo 045-2024."
```

6. **Confirmar:**
```
Click "Eliminar Permanentemente"
Confirmar en diálogo JavaScript
```

**Resultado:**
```
✅ Mensaje: "Objeto eliminado permanentemente"
✅ Registro en SecurityCodeAttempt (success=True)
✅ Registro en AuditLog con datos completos
✅ Oficina eliminada de base de datos
```

---

### Ejemplo 2: Intento Fallido con Código Incorrecto

**Escenario:** Administrador ingresa código incorrecto por error.

**Pasos:**

1. Acceder a formulario de eliminación permanente
2. Ingresar código incorrecto: `CODIGO_EQUIVOCADO`
3. Completar resto del formulario
4. Enviar

**Resultado:**
```
❌ Mensaje: "Código de seguridad incorrecto. Le quedan 2 intento(s) 
            antes del bloqueo temporal."
❌ Registro en SecurityCodeAttempt (success=False)
❌ Registro en AuditLog (action='security_violation')
⚠️ Formulario permanece accesible para reintentar
```

**Acción del usuario:**
```
1. Verificar código correcto
2. Reintentar con código correcto
3. Eliminación exitosa
```

---

### Ejemplo 3: Bloqueo por Múltiples Intentos Fallidos

**Escenario:** Administrador olvida código y hace 3 intentos fallidos.

**Intento 1:**
```
Código: CODIGO_VIEJO
Resultado: "Código incorrecto. Le quedan 2 intento(s)..."
```

**Intento 2:**
```
Código: CODIGO_ANTERIOR
Resultado: "Código incorrecto. Le quedan 1 intento(s)..."
```

**Intento 3:**
```
Código: CODIGO_PRUEBA
Resultado: "Código incorrecto. Usuario bloqueado temporalmente por 30 minutos."
```

**Intento 4 (inmediato):**
```
Al acceder al formulario:
🔒 Mensaje: "Su cuenta está bloqueada temporalmente por múltiples 
            intentos fallidos. Podrá intentar nuevamente en 29 minutos."
🔒 Todos los campos del formulario deshabilitados
```

**Solución:**

**Opción A - Esperar:**
```
Esperar 30 minutos
Bloqueo se levanta automáticamente
Reintentar con código correcto
```

**Opción B - Limpiar intentos (Superusuario):**
```python
python manage.py shell

from apps.core.models import SecurityCodeAttempt
from django.contrib.auth.models import User

user = User.objects.get(username='admin_bloqueado')
SecurityCodeAttempt.objects.filter(user=user, success=False).delete()

print("Intentos fallidos eliminados. Usuario desbloqueado.")
```

---

### Ejemplo 4: Eliminación en Lote

**Escenario:** Limpiar múltiples elementos antiguos de la papelera.

**Pasos:**

1. **Filtrar elementos antiguos:**
```
Papelera → Filtros Avanzados
Fecha de eliminación: Antes de 01/01/2023
Módulo: Todos
```

2. **Seleccionar elementos:**
```
☑ Oficina Regional Norte (eliminada 15/12/2022)
☑ Oficina Temporal Proyecto X (eliminada 20/11/2022)
☑ Oficina Piloto (eliminada 05/10/2022)
Total: 3 elementos seleccionados
```

3. **Iniciar eliminación en lote:**
```
Click "Acciones en Lote" → "Eliminar Permanentemente"
```

4. **Completar formulario:**
```
Código de Seguridad: [Código correcto]
Confirmar: ☑
Notas: "Limpieza anual de papelera. Elementos con más de 1 año 
        de antigüedad según política de retención."
```

5. **Confirmar:**
```
Click "Eliminar Permanentemente"
```

**Resultado:**
```
✅ Mensaje: "Se eliminaron permanentemente 3 elemento(s)"
✅ 1 registro en SecurityCodeAttempt (para la operación en lote)
✅ 3 registros en AuditLog (uno por cada elemento)
✅ Todos los elementos eliminados de base de datos
```

---

### Ejemplo 5: Monitoreo de Intentos Sospechosos

**Escenario:** Administrador de seguridad revisa intentos fallidos.

**Consulta en Admin:**
```
Admin → Core → Security Code Attempts
Filtrar: success = False
Ordenar: attempted_at (descendente)
```

**Resultados:**
```
Usuario          | Fecha/Hora        | IP            | Éxito
─────────────────────────────────────────────────────────────
admin_juan       | 20/01/2024 14:35  | 192.168.1.50  | ✗
admin_juan       | 20/01/2024 14:34  | 192.168.1.50  | ✗
admin_juan       | 20/01/2024 14:33  | 192.168.1.50  | ✗
admin_maria      | 20/01/2024 10:15  | 192.168.1.45  | ✗
admin_pedro      | 19/01/2024 16:20  | 192.168.1.60  | ✗
```

**Análisis:**
```
⚠️ admin_juan: 3 intentos fallidos consecutivos desde misma IP
   → Usuario bloqueado automáticamente
   → Contactar para verificar si necesita ayuda

✅ admin_maria: 1 intento fallido aislado
   → Normal, probablemente error de tipeo

✅ admin_pedro: 1 intento fallido hace 1 día
   → Sin preocupación
```

**Acción:**
```
1. Contactar a admin_juan
2. Verificar si necesita código correcto
3. Desbloquear si es necesario
4. Documentar incidente
```

---

### Ejemplo 6: Auditoría de Eliminaciones Permanentes

**Escenario:** Auditor revisa eliminaciones permanentes del mes.

**Consulta SQL:**
```sql
SELECT 
    al.timestamp,
    u.username,
    al.model_name,
    al.object_repr,
    al.changes->>'reason' as reason,
    al.changes->>'ip_address' as ip_address
FROM core_auditlog al
JOIN auth_user u ON al.user_id = u.id
WHERE al.action = 'delete'
  AND al.changes::text LIKE '%permanent_delete%'
  AND al.timestamp >= '2024-01-01'
  AND al.timestamp < '2024-02-01'
ORDER BY al.timestamp DESC;
```

**Resultados:**
```
Fecha/Hora        | Usuario      | Tipo    | Objeto                | Motivo
──────────────────────────────────────────────────────────────────────────────
20/01/2024 15:30  | admin_juan   | Oficina | Oficina Cerrada 2023  | Oficina cerrada...
18/01/2024 11:20  | admin_maria  | Bien    | Computadora #12345    | Equipo obsoleto...
15/01/2024 09:45  | admin_pedro  | Oficina | Oficina Temporal      | Proyecto finalizado...
```

**Reporte:**
```
Eliminaciones Permanentes - Enero 2024
─────────────────────────────────────────
Total: 3 eliminaciones
Por usuario:
  - admin_juan: 1
  - admin_maria: 1
  - admin_pedro: 1

Por tipo:
  - Oficinas: 2
  - Bienes: 1

Todos los registros incluyen:
✅ Motivo detallado
✅ IP de origen
✅ Código de seguridad validado
✅ Sin intentos fallidos sospechosos
```

---

### Ejemplo 7: Cambio de Código de Seguridad

**Escenario:** Rotación trimestral del código de seguridad.

**Pasos:**

1. **Generar nuevo código:**
```bash
# Usar generador de contraseñas seguras
openssl rand -base64 24
# Resultado: "Xk9mP2vL8nQ4rT6wY1zA3bC5dE7fG9hJ"
```

2. **Actualizar configuración:**
```bash
# Editar .env.prod
nano .env.prod

# Cambiar línea:
PERMANENT_DELETE_CODE=Xk9mP2vL8nQ4rT6wY1zA3bC5dE7fG9hJ
```

3. **Reiniciar aplicación:**
```bash
# Docker
docker-compose restart web

# Systemd
sudo systemctl restart patrimonio
```

4. **Verificar cambio:**
```bash
python manage.py shell
>>> from django.conf import settings
>>> settings.PERMANENT_DELETE_CODE
'Xk9mP2vL8nQ4rT6wY1zA3bC5dE7fG9hJ'
```

5. **Notificar administradores:**
```
Asunto: Nuevo Código de Seguridad - Eliminación Permanente
Fecha: 01/04/2024

Estimados administradores,

Se ha actualizado el código de seguridad para eliminación permanente
como parte de nuestra política de rotación trimestral.

El nuevo código está disponible en [ubicación segura].

Por favor, actualicen sus registros y destruyan el código anterior.

Saludos,
Equipo de Seguridad
```

6. **Documentar cambio:**
```
Registro de Cambios de Código
────────────────────────────────
Fecha: 01/04/2024
Código anterior: [Destruido]
Código nuevo: [Ver gestor de contraseñas]
Razón: Rotación trimestral programada
Notificados: admin_juan, admin_maria, admin_pedro
```

---

### Ejemplo 8: Recuperación de Datos Eliminados Permanentemente

**Escenario:** Se eliminó permanentemente un elemento por error.

**Problema:**
```
❌ Oficina "Sede Central" eliminada permanentemente
❌ No está en papelera de reciclaje
❌ Usuario solicita recuperación urgente
```

**Solución:**

**Paso 1 - Verificar en AuditLog:**
```python
from apps.core.models import AuditLog

# Buscar eliminación
audit = AuditLog.objects.filter(
    action='delete',
    object_repr__icontains='Sede Central',
    changes__permanent_delete=True
).latest('timestamp')

# Ver datos originales
original_data = audit.changes.get('original_data')
print(original_data)
```

**Paso 2 - Recrear desde datos originales:**
```python
from apps.oficinas.models import Oficina

# Extraer datos
data = original_data['fields']

# Recrear oficina
oficina = Oficina.objects.create(
    codigo=data['codigo'],
    nombre=data['nombre'],
    direccion=data['direccion'],
    telefono=data['telefono'],
    # ... otros campos
)

print(f"Oficina recreada: {oficina}")
```

**Paso 3 - Documentar recuperación:**
```python
from apps.core.models import AuditLog

AuditLog.objects.create(
    user=request.user,
    action='create',
    model_name='Oficina',
    object_id=str(oficina.id),
    object_repr=str(oficina),
    changes={
        'recovered_from_permanent_deletion': True,
        'original_audit_log_id': audit.id,
        'recovery_reason': 'Eliminación accidental. Recuperado desde AuditLog.'
    }
)
```

**Lección aprendida:**
```
✅ Siempre verificar dos veces antes de eliminar permanentemente
✅ Mantener backups regulares de base de datos
✅ AuditLog permite recuperación en casos de emergencia
```

---

### Ejemplo 9: Script de Limpieza Automática

**Escenario:** Limpiar intentos fallidos antiguos mensualmente.

**Script:** `scripts/cleanup_security_attempts.py`

```python
#!/usr/bin/env python
"""
Script para limpiar intentos de código de seguridad antiguos
Ejecutar mensualmente como tarea programada
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patrimonio.settings')
django.setup()

from apps.core.models import SecurityCodeAttempt
from django.utils import timezone
from datetime import timedelta

def cleanup_old_attempts(days=90):
    """
    Elimina intentos de código de seguridad más antiguos que X días
    
    Args:
        days: Número de días de retención (default: 90)
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Contar intentos a eliminar
    old_attempts = SecurityCodeAttempt.objects.filter(
        attempted_at__lt=cutoff_date
    )
    count = old_attempts.count()
    
    if count == 0:
        print(f"No hay intentos más antiguos que {days} días")
        return
    
    # Mostrar estadísticas antes de eliminar
    print(f"\nIntentos a eliminar: {count}")
    print(f"Fecha de corte: {cutoff_date}")
    
    stats = old_attempts.values('success').annotate(
        count=models.Count('id')
    )
    for stat in stats:
        status = 'Exitosos' if stat['success'] else 'Fallidos'
        print(f"  - {status}: {stat['count']}")
    
    # Confirmar
    confirm = input(f"\n¿Eliminar {count} intentos antiguos? (yes/no): ")
    
    if confirm.lower() == 'yes':
        deleted_count, _ = old_attempts.delete()
        print(f"\n✅ Eliminados {deleted_count} intentos antiguos")
        
        # Registrar en auditoría
        from apps.core.models import AuditLog
        from django.contrib.auth.models import User
        
        admin = User.objects.filter(is_superuser=True).first()
        if admin:
            AuditLog.objects.create(
                user=admin,
                action='delete',
                model_name='SecurityCodeAttempt',
                object_repr=f'{deleted_count} intentos antiguos',
                changes={
                    'cleanup': True,
                    'days_threshold': days,
                    'deleted_count': deleted_count
                }
            )
    else:
        print("\n❌ Operación cancelada")

if __name__ == '__main__':
    cleanup_old_attempts(days=90)
```

**Uso:**
```bash
# Ejecutar manualmente
python scripts/cleanup_security_attempts.py

# O agregar a crontab (mensual)
0 2 1 * * cd /path/to/proyecto && python scripts/cleanup_security_attempts.py
```

---

### Ejemplo 10: Dashboard de Seguridad

**Escenario:** Vista rápida del estado de seguridad.

**Template:** `templates/core/security_dashboard.html`

```python
# View
def security_dashboard(request):
    """Dashboard de seguridad para administradores"""
    if not request.user.profile.is_administrador:
        return redirect('home')
    
    # Estadísticas de últimos 30 días
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    stats = {
        'total_attempts': SecurityCodeAttempt.objects.filter(
            attempted_at__gte=thirty_days_ago
        ).count(),
        
        'failed_attempts': SecurityCodeAttempt.objects.filter(
            attempted_at__gte=thirty_days_ago,
            success=False
        ).count(),
        
        'success_rate': 0,
        
        'locked_users': [],
        
        'top_users': SecurityCodeAttempt.objects.filter(
            attempted_at__gte=thirty_days_ago
        ).values('user__username').annotate(
            attempts=Count('id')
        ).order_by('-attempts')[:5],
        
        'recent_deletions': AuditLog.objects.filter(
            action='delete',
            changes__permanent_delete=True,
            timestamp__gte=thirty_days_ago
        ).count()
    }
    
    # Calcular tasa de éxito
    if stats['total_attempts'] > 0:
        success_count = stats['total_attempts'] - stats['failed_attempts']
        stats['success_rate'] = (success_count / stats['total_attempts']) * 100
    
    # Usuarios actualmente bloqueados
    for user in User.objects.filter(profile__role='administrador'):
        is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(user)
        if is_locked:
            stats['locked_users'].append({
                'username': user.username,
                'attempts': attempts,
                'time_remaining': time_remaining
            })
    
    return render(request, 'core/security_dashboard.html', stats)
```

**Visualización:**
```
┌─────────────────────────────────────────────────────────┐
│         Dashboard de Seguridad - Últimos 30 Días       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Total de Intentos:        45                          │
│  Intentos Fallidos:        8                           │
│  Tasa de Éxito:           82.2%                        │
│  Eliminaciones Permanentes: 12                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Usuarios Bloqueados Actualmente:                      │
│    • admin_juan (15 minutos restantes)                 │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Top 5 Usuarios por Intentos:                          │
│    1. admin_maria    - 15 intentos                     │
│    2. admin_pedro    - 12 intentos                     │
│    3. admin_juan     - 10 intentos                     │
│    4. admin_lucia    - 5 intentos                      │
│    5. admin_carlos   - 3 intentos                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Conclusión

Estos ejemplos cubren los casos de uso más comunes del sistema de eliminación permanente con código de seguridad. Para más información, consultar:

- `TASK_14_SUMMARY.md` - Resumen completo de implementación
- `TASK_14_QUICK_REFERENCE.md` - Referencia rápida
- `TASK_14_VERIFICATION.md` - Lista de verificación

El sistema está diseñado para ser seguro, auditable y fácil de usar, proporcionando múltiples capas de protección contra eliminaciones accidentales o maliciosas.
