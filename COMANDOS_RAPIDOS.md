# ⚡ Comandos Rápidos - Referencia

## 🗑️ Gestión de Datos de Prueba

```bash
# Ver cuántos bienes de prueba hay
docker-compose exec web python manage.py shell -c "from apps.bienes.models import BienPatrimonial; print(f'Bienes de prueba: {BienPatrimonial.objects.filter(codigo_patrimonial__startswith=\"BP2025\").count()}')"

# Borrar datos de prueba (con confirmación)
docker-compose exec web python manage.py limpiar_datos_prueba --confirmar

# Generar nuevos datos de prueba
docker-compose exec web python manage.py generar_datos_prueba --bienes 50
```

---

## 📊 Verificación de Estadísticas

```bash
# Verificar todas las estadísticas
docker-compose exec web python verificar_estadisticas.py

# Ver total de bienes
docker-compose exec web python manage.py shell -c "from apps.bienes.models import BienPatrimonial; print(f'Total: {BienPatrimonial.objects.count()}')"

# Ver distribución por estado
docker-compose exec web python manage.py shell -c "from apps.bienes.models import BienPatrimonial; from django.db.models import Count; print(BienPatrimonial.objects.values('estado_bien').annotate(total=Count('id')))"
```

---

## 🔧 Migraciones

```bash
# Ver migraciones pendientes
docker-compose exec web python manage.py showmigrations

# Crear migración
docker-compose exec web python manage.py makemigrations

# Aplicar migraciones
docker-compose exec web python manage.py migrate

# Ver SQL de una migración
docker-compose exec web python manage.py sqlmigrate bienes 0001

# Revertir migración
docker-compose exec web python manage.py migrate bienes 0001
```

---

## 🐳 Docker

```bash
# Ver estado de contenedores
docker-compose ps

# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose down

# Reiniciar solo web
docker-compose restart web

# Ver logs
docker-compose logs web --tail=50

# Ver logs en tiempo real
docker-compose logs -f web

# Entrar al contenedor
docker-compose exec web bash
```

---

## 🔍 Inspección del Modelo

```bash
# Ver todos los campos
docker-compose exec web python manage.py shell -c "from apps.bienes.models import BienPatrimonial; [print(f'{f.name}: {\"OBLIGATORIO\" if not f.blank else \"OPCIONAL\"}') for f in BienPatrimonial._meta.fields]"

# Ver estructura del modelo
docker-compose exec web python manage.py inspectdb BienPatrimonial

# Ver configuración del admin
docker-compose exec web python manage.py shell -c "from apps.bienes.admin import BienPatrimonialAdmin; print('Columnas:', BienPatrimonialAdmin.list_display)"
```

---

## 👤 Usuarios

```bash
# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Cambiar contraseña
docker-compose exec web python manage.py changepassword admin

# Listar usuarios
docker-compose exec web python manage.py shell -c "from django.contrib.auth.models import User; [print(f'{u.username} - {u.email}') for u in User.objects.all()]"
```

---

## 🧹 Limpieza

```bash
# Limpiar archivos pyc
docker-compose exec web find . -name "*.pyc" -delete

# Limpiar cache de Python
docker-compose exec web find . -type d -name __pycache__ -exec rm -r {} +

# Limpiar datos de prueba
docker-compose exec web python manage.py limpiar_datos_prueba --confirmar

# Limpiar papelera de reciclaje
docker-compose exec web python manage.py cleanup_recycle_bin --days=30
```

---

## 📦 Base de Datos

```bash
# Backup de base de datos
docker-compose exec db pg_dump -U postgres patrimonio > backup_$(date +%Y%m%d).sql

# Restaurar base de datos
docker-compose exec -T db psql -U postgres patrimonio < backup_20251111.sql

# Conectar a PostgreSQL
docker-compose exec db psql -U postgres patrimonio

# Ver tamaño de la base de datos
docker-compose exec db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('patrimonio'));"
```

---

## 🔄 Reinicio Completo

```bash
# Reiniciar todo
docker-compose restart

# Reiniciar y reconstruir
docker-compose down
docker-compose up -d --build

# Reiniciar solo web
docker-compose restart web
```

---

## 📊 Estadísticas Rápidas

```bash
# Total de bienes
docker-compose exec web python manage.py shell -c "from apps.bienes.models import BienPatrimonial; print(BienPatrimonial.objects.count())"

# Total de oficinas
docker-compose exec web python manage.py shell -c "from apps.oficinas.models import Oficina; print(Oficina.objects.count())"

# Total de catálogo
docker-compose exec web python manage.py shell -c "from apps.catalogo.models import Catalogo; print(Catalogo.objects.count())"

# Valor total del patrimonio
docker-compose exec web python manage.py shell -c "from apps.bienes.models import BienPatrimonial; from django.db.models import Sum; print(f'S/ {BienPatrimonial.objects.aggregate(Sum(\"valor_adquisicion\"))[\"valor_adquisicion__sum\"] or 0:,.2f}')"
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
docker-compose exec web python manage.py test

# Ejecutar tests de una app
docker-compose exec web python manage.py test apps.bienes

# Ejecutar un test específico
docker-compose exec web python manage.py test apps.bienes.tests.TestBienPatrimonial

# Ejecutar con verbosidad
docker-compose exec web python manage.py test --verbosity=2
```

---

## 📝 Shell Interactivo

```bash
# Shell de Django
docker-compose exec web python manage.py shell

# Shell de Python
docker-compose exec web python

# Shell de PostgreSQL
docker-compose exec db psql -U postgres patrimonio
```

---

## 🔐 Permisos

```bash
# Configurar permisos de papelera
docker-compose exec web python manage.py setup_recycle_permissions

# Asignar permisos a usuario
docker-compose exec web python manage.py assign_recycle_permissions username

# Ver permisos de un usuario
docker-compose exec web python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='admin'); print([p.codename for p in u.user_permissions.all()])"
```

---

## 📊 Reportes

```bash
# Generar reporte de papelera
docker-compose exec web python manage.py generate_recycle_report

# Verificar tareas de Celery
docker-compose exec web python verify_celery_tasks.py

# Ver observaciones de importación
docker-compose exec web python manage.py shell -c "from apps.catalogo.models import ImportObservation; print(f'Observaciones: {ImportObservation.objects.count()}')"
```

---

## 🌐 URLs y Accesos

```bash
# Dashboard
http://localhost:8000

# Admin
http://localhost:8000/admin

# API
http://localhost:8000/api/

# Health Check
http://localhost:8000/health/

# Papelera de Reciclaje
http://localhost:8000/core/recycle-bin/
```

---

## 🔍 Búsqueda y Filtrado

```bash
# Buscar bien por código
docker-compose exec web python manage.py shell -c "from apps.bienes.models import BienPatrimonial; print(BienPatrimonial.objects.filter(codigo_patrimonial__icontains='BP2025').count())"

# Buscar por oficina
docker-compose exec web python manage.py shell -c "from apps.bienes.models import BienPatrimonial; print(BienPatrimonial.objects.filter(oficina__nombre__icontains='Admin').count())"

# Buscar por estado
docker-compose exec web python manage.py shell -c "from apps.bienes.models import BienPatrimonial; print(BienPatrimonial.objects.filter(estado_bien='B').count())"
```

---

## 📦 Importación/Exportación

```bash
# Importar catálogo
# (Usar interfaz web en /catalogo/importar/)

# Importar bienes
# (Usar interfaz web en /bienes/importar/)

# Exportar datos
# (Usar interfaz web en /reportes/)
```

---

## 🎯 Comandos Más Usados

```bash
# 1. Ver estado
docker-compose ps

# 2. Ver logs
docker-compose logs web --tail=50

# 3. Reiniciar web
docker-compose restart web

# 4. Verificar estadísticas
docker-compose exec web python verificar_estadisticas.py

# 5. Limpiar datos de prueba
docker-compose exec web python manage.py limpiar_datos_prueba --confirmar

# 6. Shell de Django
docker-compose exec web python manage.py shell

# 7. Crear migración
docker-compose exec web python manage.py makemigrations

# 8. Aplicar migración
docker-compose exec web python manage.py migrate

# 9. Crear superusuario
docker-compose exec web python manage.py createsuperuser

# 10. Backup de BD
docker-compose exec db pg_dump -U postgres patrimonio > backup.sql
```

---

## 💡 Tips

### Alias Útiles (Opcional)

Agrega a tu `.bashrc` o `.zshrc`:

```bash
alias dce='docker-compose exec'
alias dcw='docker-compose exec web'
alias dcl='docker-compose logs'
alias dcp='docker-compose ps'
alias dcr='docker-compose restart'
```

Luego puedes usar:

```bash
dcw python manage.py shell
dcl web --tail=50
dcp
dcr web
```

---

**Fecha**: 11/11/2025  
**Versión**: 1.0.0  
**Estado**: ✅ REFERENCIA RÁPIDA
