# Sistema de Backups Automáticos

## Descripción General

El Sistema de Registro de Patrimonio DRTC Puno incluye un sistema completo de backups automáticos que protege tanto la base de datos PostgreSQL como los archivos media subidos por los usuarios.

## Características

- ✅ Backups automáticos diarios a las 3:00 AM
- ✅ Compresión gzip para optimizar espacio
- ✅ Limpieza automática de backups antiguos (>7 días por defecto)
- ✅ Logging detallado de todas las operaciones
- ✅ Estructura organizada de directorios
- ✅ Scripts de restauración incluidos
- ✅ Notificaciones por email en caso de fallo
- ✅ Health checks para monitoreo

## Estructura de Directorios

```
backups/
├── db/                          # Backups de base de datos
│   ├── patrimonio_20241112_030000.sql.gz
│   ├── patrimonio_20241111_030000.sql.gz
│   └── ...
└── media/                       # Backups de archivos media
    ├── media_20241112_030000.tar.gz
    ├── media_20241111_030000.tar.gz
    └── ...

logs/
└── backup.log                   # Log de operaciones de backup
```

## Configuración

### Variables de Entorno

Agregue las siguientes variables a su archivo `.env.prod`:

```bash
# Retención de backups (días)
BACKUP_RETENTION_DAYS=7

# Configuración de email para notificaciones (opcional)
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
```

### Servicio Docker

El servicio de backup está configurado en `docker-compose.prod.yml`:

```yaml
backup:
  image: postgres:15
  restart: unless-stopped
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./backups:/backups
    - ./logs:/logs
    - media_files:/media
  # ... configuración adicional
```

## Uso

### Backups Automáticos

Los backups se ejecutan automáticamente todos los días a las 3:00 AM. No se requiere intervención manual.

Para verificar el estado del servicio de backup:

```bash
# Ver logs del servicio de backup
docker-compose -f docker-compose.prod.yml logs backup

# Ver logs detallados de backups
cat logs/backup.log
```

### Backups Manuales

Para ejecutar un backup manual inmediatamente:

**Linux/Mac:**
```bash
./scripts/backup.sh
```

**Windows:**
```cmd
scripts\backup.bat
```

### Listar Backups Disponibles

```bash
./scripts/restore.sh --list
```

Salida ejemplo:
```
=== Backups Disponibles ===

Backups de Base de Datos:
patrimonio_20241112_030000.sql.gz (45M) Nov 12 03:00
patrimonio_20241111_030000.sql.gz (44M) Nov 11 03:00
patrimonio_20241110_030000.sql.gz (43M) Nov 10 03:00

Backups de Media:
media_20241112_030000.tar.gz (120M) Nov 12 03:00
media_20241111_030000.tar.gz (118M) Nov 11 03:00
media_20241110_030000.tar.gz (115M) Nov 10 03:00
```

### Restaurar Backups

#### Restaurar Solo Base de Datos

```bash
./scripts/restore.sh --db patrimonio_20241112_030000.sql.gz
```

#### Restaurar Solo Archivos Media

```bash
./scripts/restore.sh --media media_20241112_030000.tar.gz
```

#### Restaurar Ambos

```bash
./scripts/restore.sh \
  --db patrimonio_20241112_030000.sql.gz \
  --media media_20241112_030000.tar.gz
```

**IMPORTANTE:** El script de restauración:
1. Solicita confirmación antes de proceder
2. Crea un backup de seguridad antes de restaurar
3. Registra todas las operaciones en `logs/restore.log`

## Monitoreo

### Health Checks

El servicio de backup incluye health checks que verifican:
- Existencia del archivo de log
- Que el log se haya actualizado en las últimas 25 horas

```bash
# Verificar estado del servicio
docker-compose -f docker-compose.prod.yml ps backup
```

### Logs

Los logs de backup incluyen:
- Timestamp de cada operación
- Tamaño de los archivos generados
- Número de backups eliminados
- Estadísticas de backups actuales
- Errores y advertencias

Ver logs en tiempo real:
```bash
tail -f logs/backup.log
```

### Notificaciones por Email

Si configura las variables de email, recibirá notificaciones automáticas cuando:
- Un backup falla
- Hay errores críticos en el proceso

## Configuración Avanzada

### Cambiar Hora de Backup

Edite el servicio `backup` en `docker-compose.prod.yml` y modifique la variable `TARGET_HOUR`:

```yaml
TARGET_HOUR=3;  # Cambiar a la hora deseada (0-23)
```

### Cambiar Retención de Backups

Modifique la variable de entorno:

```bash
# En .env.prod
BACKUP_RETENTION_DAYS=14  # Mantener backups por 14 días
```

### Backup a Almacenamiento Remoto

Para backups en la nube (S3, Google Cloud Storage, etc.), puede:

1. Instalar herramientas CLI (aws-cli, gsutil, etc.)
2. Modificar `scripts/backup.sh` para incluir upload
3. Configurar credenciales en variables de entorno

Ejemplo para AWS S3:

```bash
# En scripts/backup.sh, después de crear backups
aws s3 sync /backups s3://mi-bucket/backups/ --delete
```

## Restauración de Desastres

### Escenario 1: Pérdida Total de Base de Datos

```bash
# 1. Detener servicios
docker-compose -f docker-compose.prod.yml down

# 2. Eliminar volumen de base de datos
docker volume rm patrimonio_postgres_data

# 3. Iniciar solo base de datos
docker-compose -f docker-compose.prod.yml up -d db

# 4. Esperar que esté lista
docker-compose -f docker-compose.prod.yml exec db pg_isready

# 5. Restaurar backup más reciente
./scripts/restore.sh --db patrimonio_YYYYMMDD_HHMMSS.sql.gz

# 6. Iniciar todos los servicios
docker-compose -f docker-compose.prod.yml up -d
```

### Escenario 2: Corrupción de Datos

```bash
# 1. Identificar el último backup bueno
./scripts/restore.sh --list

# 2. Restaurar ese backup (crea backup de seguridad automáticamente)
./scripts/restore.sh --db patrimonio_YYYYMMDD_HHMMSS.sql.gz

# 3. Verificar datos restaurados
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
```

### Escenario 3: Migración a Nuevo Servidor

```bash
# En servidor antiguo:
# 1. Crear backup manual
./scripts/backup.sh

# 2. Copiar directorio backups/ al nuevo servidor
scp -r backups/ user@new-server:/path/to/project/

# En servidor nuevo:
# 3. Configurar sistema
./scripts/prepare-ubuntu-server.sh
./scripts/configure-env.sh

# 4. Iniciar servicios
docker-compose -f docker-compose.prod.yml up -d

# 5. Restaurar backups
./scripts/restore.sh --db patrimonio_YYYYMMDD_HHMMSS.sql.gz
./scripts/restore.sh --media media_YYYYMMDD_HHMMSS.tar.gz
```

## Troubleshooting

### Problema: Backups no se están creando

**Verificar:**
```bash
# 1. Estado del servicio
docker-compose -f docker-compose.prod.yml ps backup

# 2. Logs del servicio
docker-compose -f docker-compose.prod.yml logs backup

# 3. Permisos del directorio
ls -la backups/
```

**Solución:**
```bash
# Reiniciar servicio de backup
docker-compose -f docker-compose.prod.yml restart backup
```

### Problema: Espacio en disco insuficiente

**Verificar:**
```bash
# Espacio disponible
df -h

# Tamaño de backups
du -sh backups/
```

**Solución:**
```bash
# Reducir retención de backups
# En .env.prod
BACKUP_RETENTION_DAYS=3

# O limpiar backups manualmente
find backups/db -name "*.sql.gz" -mtime +3 -delete
find backups/media -name "*.tar.gz" -mtime +3 -delete
```

### Problema: Restauración falla

**Verificar:**
```bash
# 1. Integridad del archivo de backup
gunzip -t backups/db/patrimonio_YYYYMMDD_HHMMSS.sql.gz

# 2. Espacio disponible
df -h

# 3. Servicio de base de datos
docker-compose -f docker-compose.prod.yml ps db
```

**Solución:**
```bash
# Si el backup está corrupto, usar backup anterior
./scripts/restore.sh --list
./scripts/restore.sh --db patrimonio_OLDER_BACKUP.sql.gz
```

### Problema: Notificaciones de email no funcionan

**Verificar:**
```bash
# Variables de entorno configuradas
grep EMAIL .env.prod

# Logs de Django
docker-compose -f docker-compose.prod.yml logs web | grep email
```

**Solución:**
```bash
# Probar envío de email manualmente
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

## Mejores Prácticas

1. **Verificar backups regularmente**: Pruebe la restauración al menos una vez al mes
2. **Monitorear espacio en disco**: Configure alertas cuando el espacio sea bajo
3. **Mantener backups offsite**: Copie backups a almacenamiento remoto
4. **Documentar procedimientos**: Mantenga documentación actualizada
5. **Probar recuperación de desastres**: Simule escenarios de fallo
6. **Rotar credenciales**: Cambie contraseñas de base de datos periódicamente
7. **Encriptar backups sensibles**: Use GPG para backups con datos sensibles

## Comandos Útiles

```bash
# Ver tamaño total de backups
du -sh backups/

# Contar número de backups
find backups/db -name "*.sql.gz" | wc -l
find backups/media -name "*.tar.gz" | wc -l

# Ver backup más reciente
ls -lt backups/db/*.sql.gz | head -1
ls -lt backups/media/*.tar.gz | head -1

# Verificar integridad de todos los backups
for file in backups/db/*.sql.gz; do gunzip -t "$file" && echo "$file OK"; done

# Crear backup manual con nombre personalizado
docker-compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U postgres patrimonio | gzip > backups/db/manual_backup_$(date +%Y%m%d).sql.gz
```

## Soporte

Para problemas o preguntas sobre el sistema de backups:

1. Revise los logs: `logs/backup.log`
2. Consulte esta documentación
3. Revise los issues en el repositorio
4. Contacte al equipo de desarrollo

## Referencias

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
- [Cron Scheduling](https://crontab.guru/)
