# Guía de Inicio Rápido - Sistema de Papelera de Reciclaje

## Introducción

Esta guía te ayudará a poner en marcha el sistema de papelera de reciclaje en 10 minutos.

## Requisitos Previos

- Django 3.2+
- Python 3.8+
- PostgreSQL o MySQL
- Redis (para Celery)
- Celery instalado

## Instalación en 5 Pasos

### Paso 1: Configurar Variables de Entorno

Crea o edita tu archivo `.env`:

```bash
# Código de seguridad (CAMBIAR EN PRODUCCIÓN)
PERMANENT_DELETE_CODE=MiCodigoSeguro2025!

# Configuración básica
RECYCLE_BIN_DEFAULT_RETENTION_DAYS=30
RECYCLE_BIN_AUTO_DELETE_ENABLED=True

# Email (opcional para desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
```

### Paso 2: Ejecutar Migraciones

```bash
python manage.py migrate
```

Esto creará las tablas necesarias:
- `core_recyclebin`
- `core_recyclebinconfig`
- `core_deletionauditlog`

### Paso 3: Configurar el Sistema

```bash
# Configuración inicial
python manage.py setup_recycle_bin

# Configurar permisos
python manage.py setup_recycle_permissions
```

### Paso 4: Asignar Permisos a Usuarios

```bash
# Dar permisos de admin a tu usuario
python manage.py assign_recycle_permissions \
  --user=tu_usuario \
  --role=admin
```

### Paso 5: Iniciar Celery (Opcional pero Recomendado)

```bash
# En una terminal
celery -A patrimonio worker --loglevel=info

# En otra terminal
celery -A patrimonio beat --loglevel=info
```

## Verificación

### 1. Verificar que el Sistema Funciona

```bash
python manage.py shell
```

```python
# En el shell de Django
from apps.core.models import RecycleBinConfig
from apps.oficinas.models import Oficina
from django.contrib.auth.models import User

# Verificar configuración
configs = RecycleBinConfig.objects.all()
print(f"Configuraciones creadas: {configs.count()}")

# Probar soft delete
user = User.objects.first()
oficina = Oficina.objects.first()
oficina.soft_delete(user=user, reason="Prueba")
print(f"Oficina eliminada: {oficina.is_deleted}")

# Verificar en papelera
from apps.core.models import RecycleBin
items = RecycleBin.objects.all()
print(f"Elementos en papelera: {items.count()}")

# Restaurar
oficina.restore(user=user)
print(f"Oficina restaurada: {not oficina.is_deleted}")
```

### 2. Acceder a la Interfaz Web

1. Inicia el servidor: `python manage.py runserver`
2. Accede a: `http://localhost:8000/papelera/`
3. Deberías ver la interfaz de papelera

### 3. Verificar Tareas de Celery

```bash
# Ver tareas programadas
celery -A patrimonio inspect scheduled

# Deberías ver:
# - cleanup-recycle-bin
# - send-recycle-warnings
# - send-final-warnings
```

## Uso Básico

### Eliminar un Registro

```python
# En tu código
from apps.core.services import RecycleBinService

# Eliminar usando el servicio
RecycleBinService.soft_delete_object(
    obj=mi_objeto,
    user=request.user,
    reason="Ya no es necesario"
)
```

O simplemente:

```python
# Usando el método del modelo
mi_objeto._current_user = request.user
mi_objeto.delete()  # Usa soft delete automáticamente
```

### Restaurar un Registro

```python
from apps.core.models import RecycleBin

# Obtener entrada de papelera
entry = RecycleBin.objects.get(pk=123)

# Restaurar
RecycleBinService.restore_object(
    recycle_bin_entry=entry,
    user=request.user
)
```

### Eliminar Permanentemente

```python
# Solo administradores con código de seguridad
RecycleBinService.permanent_delete(
    recycle_bin_entry=entry,
    user=request.user,
    security_code="MiCodigoSeguro2025!"
)
```

## Configuración Rápida por Módulo

### Oficinas (45 días de retención)

```bash
python manage.py setup_recycle_bin \
  --module=oficinas \
  --retention-days=45
```

### Bienes (90 días, sin auto-delete)

```bash
python manage.py setup_recycle_bin \
  --module=bienes \
  --retention-days=90 \
  --no-auto-delete
```

### Catálogo (30 días, por defecto)

```bash
python manage.py setup_recycle_bin \
  --module=catalogo
```

## Comandos Útiles

### Ver Elementos en Papelera

```bash
python manage.py shell
```

```python
from apps.core.models import RecycleBin
items = RecycleBin.objects.all()
for item in items:
    print(f"{item.module_name}: {item.object_repr} - {item.deleted_at}")
```

### Limpiar Papelera Manualmente

```bash
# Simulación (no elimina)
python manage.py cleanup_recycle_bin --dry-run

# Limpieza real
python manage.py cleanup_recycle_bin
```

### Generar Reporte

```bash
python manage.py generate_recycle_report --format=pdf
```

## Integración con Vistas Existentes

### Actualizar Vista de Eliminación

```python
# Antes
class OficinaDeleteView(DeleteView):
    model = Oficina
    success_url = reverse_lazy('oficinas:lista')

# Después (con soft delete)
class OficinaDeleteView(DeleteView):
    model = Oficina
    success_url = reverse_lazy('oficinas:lista')
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj._current_user = request.user
        obj.delete()  # Usa soft delete automáticamente
        messages.success(request, 'Oficina movida a papelera')
        return redirect(self.success_url)
```

### Agregar Enlace a Papelera en Template

```html
<!-- En tu template base -->
<nav>
    <a href="{% url 'core:recycle_bin_list' %}">
        Papelera
        <span class="badge">{{ recycle_bin_count }}</span>
    </a>
</nav>
```

## Personalización Rápida

### Cambiar Días de Retención

```python
# En settings.py
RECYCLE_BIN_CONFIG = {
    'DEFAULT_RETENTION_DAYS': 60,  # Cambiar de 30 a 60
}
```

### Deshabilitar Notificaciones

```python
# En settings.py
RECYCLE_BIN_CONFIG = {
    'EMAIL_NOTIFICATIONS': False,
}
```

### Cambiar Código de Seguridad

```bash
# En .env
PERMANENT_DELETE_CODE=NuevoCodigoSeguro2025!
```

## Troubleshooting Rápido

### Problema: "No module named 'apps.core'"

**Solución**: Asegúrate de estar en el directorio raíz del proyecto.

### Problema: Migraciones fallan

**Solución**: 
```bash
python manage.py makemigrations core
python manage.py migrate core
```

### Problema: Celery no inicia

**Solución**: Verifica que Redis esté corriendo:
```bash
redis-cli ping
# Debería responder: PONG
```

### Problema: No veo elementos en papelera

**Solución**: Verifica que estés usando soft delete:
```python
# Correcto
obj.soft_delete(user=user)

# O
obj._current_user = user
obj.delete()
```

### Problema: Código de seguridad no funciona

**Solución**: Verifica la configuración:
```python
python manage.py shell
>>> from django.conf import settings
>>> print(settings.PERMANENT_DELETE_CODE)
```

## Próximos Pasos

1. **Lee la Guía de Usuario**: `docs/RECYCLE_BIN_USER_GUIDE.md`
2. **Configura Notificaciones**: `docs/RECYCLE_BIN_CONFIGURATION.md`
3. **Aprende Comandos Avanzados**: `docs/RECYCLE_BIN_COMMANDS.md`
4. **Revisa la Guía Técnica**: `docs/RECYCLE_BIN_TECHNICAL_GUIDE.md`

## Checklist de Implementación

- [ ] Variables de entorno configuradas
- [ ] Migraciones ejecutadas
- [ ] Sistema configurado con `setup_recycle_bin`
- [ ] Permisos configurados
- [ ] Permisos asignados a usuarios
- [ ] Celery iniciado (worker + beat)
- [ ] Código de seguridad cambiado en producción
- [ ] Configuración por módulo ajustada
- [ ] Vistas actualizadas para usar soft delete
- [ ] Enlaces a papelera agregados en templates
- [ ] Notificaciones configuradas
- [ ] Tests ejecutados
- [ ] Documentación revisada

## Recursos Adicionales

- **Documentación Completa**: Ver carpeta `docs/`
- **Ejemplos de Código**: Ver `apps/core/services.py`
- **Tests**: Ver `tests/test_recycle_bin*.py`
- **Soporte**: soporte@patrimonio.gob

## Comandos de Referencia Rápida

```bash
# Configuración inicial
python manage.py setup_recycle_bin
python manage.py setup_recycle_permissions

# Asignar permisos
python manage.py assign_recycle_permissions --user=admin --role=admin

# Limpieza
python manage.py cleanup_recycle_bin --dry-run
python manage.py cleanup_recycle_bin

# Reportes
python manage.py generate_recycle_report --format=pdf

# Celery
celery -A patrimonio worker --loglevel=info
celery -A patrimonio beat --loglevel=info

# Verificar configuración
python manage.py shell
>>> from apps.core.models import RecycleBinConfig
>>> RecycleBinConfig.objects.all()
```

## Contacto

¿Necesitas ayuda? Contacta a:
- **Email**: soporte@patrimonio.gob
- **Documentación**: Ver carpeta `docs/`
- **Issues**: [URL del repositorio]

---

**¡Listo!** Tu sistema de papelera de reciclaje está configurado y funcionando.
