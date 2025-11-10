# Guía Rápida: Sistema de Protección de Seguridad

## 🚀 Inicio Rápido

### Para Administradores

#### 1. Configurar Código de Seguridad
```python
# En .env o settings.py
PERMANENT_DELETE_CODE = "TU_CODIGO_SEGURO_AQUI"
```

#### 2. Configurar CAPTCHA (Opcional)
```python
# Obtener claves en: https://www.google.com/recaptcha/admin
RECAPTCHA_SITE_KEY = "tu_site_key"
RECAPTCHA_SECRET_KEY = "tu_secret_key"
```

#### 3. Acceder al Dashboard de Seguridad
```
URL: /core/seguridad/monitoreo/
Permisos: Administrador o Auditor
```

## 📊 Niveles de Bloqueo

| Nivel | Intentos Fallidos | Duración Bloqueo | Desbloqueo |
|-------|------------------|------------------|------------|
| Normal | 0-2 | 30 minutos | Automático |
| Medio | 3-5 | 30 minutos | Automático |
| Alto | 6-9 | 60 minutos | Automático |
| **Crítico** | 10+ | 120 minutos | **Requiere Admin** |

## 🔐 Flujo de Usuario

### Eliminación Permanente Normal
1. Usuario accede a papelera
2. Selecciona elemento a eliminar permanentemente
3. Ingresa código de seguridad
4. ✅ Eliminación exitosa

### Con Intentos Fallidos
1. Usuario ingresa código incorrecto
2. ⚠️ Sistema muestra: "Le quedan 2 intentos"
3. Segundo intento fallido
4. ⚠️ Sistema muestra: "Le queda 1 intento. Se requerirá CAPTCHA"
5. Tercer intento fallido
6. 🔒 Usuario bloqueado por 30 minutos

### Nivel Crítico
1. Usuario acumula 10+ intentos fallidos en 24h
2. 🔒 Bloqueo de 120 minutos
3. ⚠️ Mensaje: "Contacte a un administrador"
4. Admin debe desbloquear manualmente

## 🛠️ Acciones de Administrador

### Desbloquear Usuario
```
1. Ir a: /core/seguridad/monitoreo/
2. Buscar usuario en tabla "Usuarios con Más Intentos Fallidos"
3. Click en botón "Desbloquear"
4. Confirmar acción
```

### Ver Detalle de Intento
```
1. En dashboard, tabla "Intentos Recientes"
2. Click en botón "Ver" del intento
3. Ver información completa:
   - IP, User-Agent, Session ID
   - Intentos relacionados
   - Resumen de seguridad del usuario
```

### Exportar Reporte
```
1. Ir a: /core/seguridad/monitoreo/
2. Seleccionar período (1h, 6h, 24h, 3d, 7d)
3. Copiar datos de tablas o tomar screenshot
```

## 📈 Métricas Clave

### Dashboard Principal
- **Total de Intentos**: Todos los intentos en el período
- **Intentos Fallidos**: Intentos con código incorrecto
- **Intentos Exitosos**: Eliminaciones completadas
- **Usuarios Bloqueados**: Usuarios actualmente bloqueados

### Métricas Adicionales
- **Bloqueados por Rate Limit**: Excedieron 5 intentos/10min
- **Requirieron CAPTCHA**: Tuvieron 2+ intentos fallidos
- **Accesos No Autorizados**: Usuarios sin permisos

## 🔍 Casos de Uso

### Caso 1: Usuario Olvidó el Código
**Síntoma**: Múltiples intentos fallidos del mismo usuario
**Acción**:
1. Verificar en dashboard que es usuario legítimo
2. Proporcionar código correcto al usuario
3. Si está bloqueado, desbloquear manualmente

### Caso 2: Ataque de Fuerza Bruta
**Síntoma**: Múltiples intentos desde misma IP, diferentes usuarios
**Acción**:
1. Revisar tabla "IPs con Más Intentos Fallidos"
2. Verificar User-Agent y patrones
3. Considerar bloqueo de IP a nivel de firewall
4. Cambiar PERMANENT_DELETE_CODE

### Caso 3: Usuario Legítimo Bloqueado
**Síntoma**: Usuario reporta no poder eliminar
**Acción**:
1. Verificar en dashboard estado del usuario
2. Revisar historial de intentos
3. Desbloquear si es legítimo
4. Proporcionar código correcto

### Caso 4: Actividad Sospechosa
**Síntoma**: Picos inusuales en gráfico de intentos
**Acción**:
1. Revisar período específico en dashboard
2. Identificar usuarios/IPs involucrados
3. Revisar logs de auditoría detallados
4. Tomar medidas preventivas

## ⚙️ Configuración Avanzada

### Ajustar Rate Limiting
```python
# En apps/core/models.py - SecurityCodeAttempt.check_rate_limit()
is_limited, count, time = SecurityCodeAttempt.check_rate_limit(
    user,
    max_requests=5,      # Cambiar límite
    time_window_minutes=10  # Cambiar ventana
)
```

### Ajustar Umbral CAPTCHA
```python
# En apps/core/models.py - SecurityCodeAttempt.requires_captcha_validation()
requires = SecurityCodeAttempt.requires_captcha_validation(
    user,
    captcha_threshold=2  # Cambiar umbral
)
```

### Ajustar Niveles de Bloqueo
```python
# En apps/core/models.py - SecurityCodeAttempt.get_lockout_level()
# Modificar los umbrales en la función:
if total_failures >= 10:  # Nivel Crítico
if total_failures >= 6:   # Nivel Alto
if total_failures >= 3:   # Nivel Medio
```

## 🚨 Alertas y Notificaciones

### Eventos que Generan Alertas
1. Usuario alcanza nivel crítico
2. Más de 10 intentos fallidos en 1 hora
3. Múltiples intentos desde misma IP
4. Intentos de acceso no autorizado

### Revisar Alertas
```
1. Dashboard → Sección "Usuarios con Más Intentos Fallidos"
2. Filtrar por nivel "Crítico"
3. Revisar detalles de cada caso
```

## 📱 Acceso Móvil

El dashboard es responsive y funciona en dispositivos móviles:
- Tablas con scroll horizontal
- Gráficos adaptables
- Botones táctiles optimizados

## 🔄 Mantenimiento

### Limpieza de Logs Antiguos
```python
# Ejecutar periódicamente (ej: mensualmente)
from apps.core.models import SecurityCodeAttempt
from datetime import timedelta
from django.utils import timezone

# Eliminar intentos de más de 90 días
cutoff = timezone.now() - timedelta(days=90)
SecurityCodeAttempt.objects.filter(attempted_at__lt=cutoff).delete()
```

### Rotación de Código de Seguridad
```python
# Cambiar periódicamente (ej: trimestralmente)
# 1. Generar nuevo código seguro
# 2. Actualizar en .env o settings.py
# 3. Notificar a administradores
# 4. Reiniciar aplicación
```

## 📞 Soporte

### Problemas Comunes

**P: Usuario no puede eliminar nada**
R: Verificar si está bloqueado en dashboard y desbloquear

**P: CAPTCHA no aparece**
R: Verificar configuración de RECAPTCHA_SITE_KEY

**P: Dashboard no carga**
R: Verificar permisos de usuario (debe ser Admin o Auditor)

**P: Todos los intentos fallan**
R: Verificar que PERMANENT_DELETE_CODE esté configurado correctamente

## 🎓 Mejores Prácticas

1. **Revisar dashboard diariamente** para detectar actividad sospechosa
2. **Cambiar código de seguridad** cada 3 meses
3. **Mantener logs** por al menos 90 días
4. **Documentar desbloqueos** manuales con razón
5. **Capacitar usuarios** sobre el código de seguridad
6. **Monitorear IPs** con múltiples intentos fallidos
7. **Configurar CAPTCHA** en producción
8. **Establecer alertas** para nivel crítico

## 📊 KPIs de Seguridad

Métricas a monitorear:
- **Tasa de éxito**: Debe ser > 90%
- **Usuarios bloqueados**: Debe ser < 5% del total
- **Intentos por rate limit**: Debe ser < 1% del total
- **Accesos no autorizados**: Debe ser 0

## ✅ Checklist de Implementación

- [ ] Configurar PERMANENT_DELETE_CODE
- [ ] Configurar RECAPTCHA (opcional)
- [ ] Verificar acceso a dashboard
- [ ] Probar eliminación permanente
- [ ] Probar bloqueo por intentos fallidos
- [ ] Probar desbloqueo manual
- [ ] Capacitar administradores
- [ ] Documentar código de seguridad
- [ ] Establecer proceso de rotación
- [ ] Configurar monitoreo periódico
