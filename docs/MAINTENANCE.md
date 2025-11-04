# Guía de Mantenimiento - Sistema de Registro de Patrimonio

## Tareas de Mantenimiento Rutinario

### Diarias

#### 1. Verificación de Estado del Sistema
```bash
# Ejecutar script de monitoreo
./scripts/monitor.sh

# Verificar logs de errores
docker-compose -f docker-compose.prod.yml logs --tail=100 web | grep ERROR

# Verificar espacio en disco
df -h
```

#### 2. Verificación de Backups
```bash
# Verificar que se creó backup automático
ls -la backups/ | head -5

# Verificar integridad del último backup
gunzip -t backups/db_backup_$(date +%Y%m%d)*.sql.gz
```

### Semanales

#### 1. Limpieza de Logs
```bash
# Limpiar logs antiguos (mantener últimos 7 días)
find logs/ -name "*.log" -mtime +7 -delete

# Rotar logs de nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reopen
```

#### 2. Actualización de Certificados SSL
```bash
# Verificar expiración de certificados
openssl x509 -enddate -noout -in certbot/conf/live/tu-dominio.com/fullchain.pem

# Renovar si es necesario (automático con cron)
docker-compose -f docker-compose.prod.yml run --rm certbot renew
```

#### 3. Optimización de Base de Datos
```bash
# Ejecutar VACUUM y ANALYZE en PostgreSQL
docker-compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# Verificar estadísticas de la base de datos
docker-compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT schemaname,tablename,n_tup_ins,n_tup_upd,n_tup_del FROM pg_stat_user_tables;"
```

### Mensuales

#### 1. Actualización del Sistema
```bash
# Hacer backup completo antes de actualizar
./scripts/backup.sh

# Actualizar imágenes Docker
docker-compose -f docker-compose.prod.yml pull

# Actualizar aplicación
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Ejecutar migraciones
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

#### 2. Limpieza de Archivos Temporales
```bash
# Limpiar archivos temporales de Django
docker-compose -f docker-compose.prod.yml exec web find /tmp -name "*.tmp" -mtime +7 -delete

# Limpiar caché de Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHDB
```

#### 3. Auditoría de Seguridad
```bash
# Verificar usuarios activos
docker-compose -f docker-compose.prod.yml exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print('Usuarios activos:', User.objects.filter(is_active=True).count())
print('Últimos logins:', User.objects.filter(last_login__isnull=False).order_by('-last_login')[:5].values_list('username', 'last_login'))
"

# Verificar intentos de login fallidos
docker-compose -f docker-compose.prod.yml logs nginx | grep "401\|403" | tail -20
```

## Procedimientos de Backup y Restauración

### Backup Manual

#### Backup Completo
```bash
# Ejecutar script de backup
./scripts/backup.sh

# Verificar archivos creados
ls -la backups/ | tail -5
```

#### Backup Solo Base de Datos
```bash
# Crear backup de base de datos
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T db pg_dump \
    -U $POSTGRES_USER -d $POSTGRES_DB \
    --no-owner --no-privileges --clean --if-exists \
    | gzip > backups/manual_db_backup_$DATE.sql.gz
```

#### Backup Solo Archivos Media
```bash
# Crear backup de archivos media
DATE=$(date +%Y%m%d_%H%M%S)
docker run --rm \
    -v patrimonio_media_files:/data \
    -v $(pwd)/backups:/backup \
    alpine tar czf /backup/manual_media_backup_$DATE.tar.gz -C /data .
```

### Restauración

#### Restauración Completa
```bash
# Usar script de restauración
./scripts/restore.sh YYYYMMDD_HHMMSS

# Ejemplo:
./scripts/restore.sh 20241104_143000
```

#### Restauración Solo Base de Datos
```bash
# Detener servicios web
docker-compose -f docker-compose.prod.yml stop web celery celery-beat

# Restaurar base de datos
gunzip -c backups/db_backup_FECHA.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Reiniciar servicios
docker-compose -f docker-compose.prod.yml start web celery celery-beat
```

## Monitoreo y Alertas

### Configuración de Monitoreo

#### Script de Monitoreo Automático
El sistema incluye un script de monitoreo que verifica:
- Estado de contenedores Docker
- Salud de la aplicación
- Uso de disco y memoria
- Expiración de certificados SSL
- Existencia de backups recientes

```bash
# Configurar en crontab para ejecutar cada 5 minutos
crontab -e

# Agregar línea:
*/5 * * * * /ruta/al/proyecto/scripts/monitor.sh
```

#### Configuración de Alertas por Email
Editar `scripts/monitor.sh`:

```bash
ALERT_EMAIL="admin@tu-dominio.com"
```

### Métricas Importantes

#### Uso de Recursos
```bash
# Verificar uso de CPU y memoria por contenedor
docker stats --no-stream

# Verificar uso de disco
df -h
du -sh backups/ logs/ media/
```

#### Performance de Base de Datos
```bash
# Consultas lentas
docker-compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Conexiones activas
docker-compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';"
```

#### Logs de Aplicación
```bash
# Errores recientes
docker-compose -f docker-compose.prod.yml logs --tail=100 web | grep ERROR

# Accesos recientes
docker-compose -f docker-compose.prod.yml logs --tail=100 nginx | grep -E "GET|POST"

# Tareas Celery
docker-compose -f docker-compose.prod.yml logs --tail=100 celery
```

## Solución de Problemas

### Problemas Comunes

#### 1. Aplicación No Responde
```bash
# Verificar estado de contenedores
docker-compose -f docker-compose.prod.yml ps

# Verificar logs
docker-compose -f docker-compose.prod.yml logs web

# Reiniciar servicios
docker-compose -f docker-compose.prod.yml restart web
```

#### 2. Base de Datos Lenta
```bash
# Verificar conexiones
docker-compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT * FROM pg_stat_activity;"

# Optimizar base de datos
docker-compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# Reiniciar PostgreSQL
docker-compose -f docker-compose.prod.yml restart db
```

#### 3. Espacio en Disco Lleno
```bash
# Limpiar logs antiguos
find logs/ -name "*.log" -mtime +7 -delete

# Limpiar backups antiguos
find backups/ -name "*.sql.gz" -mtime +30 -delete
find backups/ -name "*.tar.gz" -mtime +30 -delete

# Limpiar imágenes Docker no utilizadas
docker system prune -a
```

#### 4. Certificado SSL Expirado
```bash
# Renovar certificado
docker-compose -f docker-compose.prod.yml run --rm certbot renew

# Reiniciar nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Procedimientos de Emergencia

#### Restauración Rápida
```bash
# 1. Detener todos los servicios
docker-compose -f docker-compose.prod.yml down

# 2. Restaurar desde backup más reciente
LATEST_BACKUP=$(ls -t backups/db_backup_*.sql.gz | head -1)
./scripts/restore.sh $(basename $LATEST_BACKUP .sql.gz | sed 's/db_backup_//')

# 3. Verificar funcionamiento
curl https://tu-dominio.com/health/
```

#### Rollback de Actualización
```bash
# 1. Hacer backup del estado actual
./scripts/backup.sh

# 2. Volver a versión anterior
git checkout HEAD~1

# 3. Reconstruir y desplegar
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Restaurar base de datos si es necesario
# (usar backup anterior a la actualización)
```

## Optimización de Performance

### Base de Datos

#### Índices
```sql
-- Verificar índices faltantes
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public' 
ORDER BY n_distinct DESC;

-- Crear índices adicionales si es necesario
CREATE INDEX CONCURRENTLY idx_bienes_codigo_patrimonial ON bienes_bienpatrimonial(codigo_patrimonial);
CREATE INDEX CONCURRENTLY idx_bienes_oficina ON bienes_bienpatrimonial(oficina_id);
```

#### Configuración PostgreSQL
```bash
# Editar configuración PostgreSQL
docker-compose -f docker-compose.prod.yml exec db bash
echo "shared_preload_libraries = 'pg_stat_statements'" >> /var/lib/postgresql/data/postgresql.conf
echo "pg_stat_statements.track = all" >> /var/lib/postgresql/data/postgresql.conf
```

### Aplicación Django

#### Cache
```python
# Configurar cache en settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

#### Static Files
```bash
# Optimizar archivos estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec web python manage.py compress
```

### Nginx

#### Configuración de Cache
```nginx
# Agregar a nginx.conf
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Actualizaciones y Migraciones

### Proceso de Actualización

#### 1. Preparación
```bash
# Hacer backup completo
./scripts/backup.sh

# Verificar estado actual
docker-compose -f docker-compose.prod.yml ps
curl https://tu-dominio.com/health/detailed/
```

#### 2. Actualización
```bash
# Obtener nueva versión
git fetch origin
git checkout v2.0.0  # o la versión deseada

# Revisar cambios
git log --oneline HEAD~10..HEAD
```

#### 3. Migración
```bash
# Ejecutar migraciones
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --dry-run
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Actualizar archivos estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

#### 4. Verificación
```bash
# Verificar funcionamiento
curl https://tu-dominio.com/health/detailed/

# Verificar logs
docker-compose -f docker-compose.prod.yml logs --tail=50 web
```

### Rollback de Migraciones
```bash
# Ver migraciones aplicadas
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations

# Hacer rollback a migración específica
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate app_name 0001
```

## Contacto y Escalación

### Niveles de Soporte

#### Nivel 1 - Administrador del Sistema
- Monitoreo diario
- Backups rutinarios
- Problemas básicos de conectividad

#### Nivel 2 - Administrador de Base de Datos
- Optimización de consultas
- Problemas de performance
- Corrupción de datos

#### Nivel 3 - Desarrollador
- Bugs de aplicación
- Nuevas funcionalidades
- Migraciones complejas

### Información de Contacto
- **Soporte Técnico**: soporte@tu-dominio.com
- **Emergencias**: +51-XXX-XXXXXX
- **Documentación**: https://tu-dominio.com/docs/
- **Repository**: https://github.com/tu-organizacion/sistema-patrimonio