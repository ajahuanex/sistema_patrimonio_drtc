# Guía Rápida - Sistema de Backups

## Comandos Esenciales

### Ver Estado del Sistema de Backups

```bash
# Ver logs del servicio de backup
docker-compose -f docker-compose.prod.yml logs backup

# Ver últimas líneas del log de backup
tail -20 logs/backup.log

# Ver estado del servicio
docker-compose -f docker-compose.prod.yml ps backup
```

### Ejecutar Backup Manual

```bash
# Linux/Mac
./scripts/backup.sh

# Windows
scripts\backup.bat
```

### Listar Backups Disponibles

```bash
./scripts/restore.sh --list
```

### Restaurar Backups

```bash
# Solo base de datos
./scripts/restore.sh --db patrimonio_20241112_030000.sql.gz

# Solo archivos media
./scripts/restore.sh --media media_20241112_030000.sql.gz

# Ambos
./scripts/restore.sh --db patrimonio_20241112_030000.sql.gz --media media_20241112_030000.tar.gz
```

## Estructura de Archivos

```
backups/
├── db/                    # Backups de PostgreSQL (.sql.gz)
└── media/                 # Backups de archivos media (.tar.gz)

logs/
├── backup.log            # Log de operaciones de backup
└── restore.log           # Log de operaciones de restauración
```

## Configuración

### Variables de Entorno (.env.prod)

```bash
# Días de retención de backups (default: 7)
BACKUP_RETENTION_DAYS=7

# Email para notificaciones (opcional)
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
```

## Horario de Backups

- **Automáticos**: Todos los días a las 3:00 AM
- **Retención**: 7 días por defecto (configurable)
- **Limpieza**: Automática de backups antiguos

## Verificación Rápida

```bash
# ¿Cuántos backups tengo?
find backups/db -name "*.sql.gz" | wc -l
find backups/media -name "*.tar.gz" | wc -l

# ¿Cuánto espacio ocupan?
du -sh backups/

# ¿Cuál es el backup más reciente?
ls -lt backups/db/*.sql.gz | head -1
ls -lt backups/media/*.tar.gz | head -1

# ¿El último backup fue exitoso?
tail -5 logs/backup.log
```

## Troubleshooting Rápido

### Problema: No se están creando backups

```bash
# 1. Verificar servicio
docker-compose -f docker-compose.prod.yml ps backup

# 2. Ver logs
docker-compose -f docker-compose.prod.yml logs backup

# 3. Reiniciar servicio
docker-compose -f docker-compose.prod.yml restart backup
```

### Problema: Espacio en disco lleno

```bash
# 1. Ver espacio disponible
df -h

# 2. Reducir retención (editar .env.prod)
BACKUP_RETENTION_DAYS=3

# 3. Reiniciar servicio de backup
docker-compose -f docker-compose.prod.yml restart backup
```

### Problema: Restauración falla

```bash
# 1. Verificar integridad del backup
gunzip -t backups/db/patrimonio_YYYYMMDD_HHMMSS.sql.gz

# 2. Verificar servicio de DB
docker-compose -f docker-compose.prod.yml ps db

# 3. Intentar con backup anterior
./scripts/restore.sh --list
./scripts/restore.sh --db BACKUP_ANTERIOR.sql.gz
```

## Mejores Prácticas

1. ✅ Verificar backups semanalmente
2. ✅ Probar restauración mensualmente
3. ✅ Monitorear espacio en disco
4. ✅ Mantener backups offsite (S3, etc.)
5. ✅ Documentar procedimientos de recuperación

## Contacto y Soporte

- Documentación completa: `docs/BACKUP_SYSTEM.md`
- Logs: `logs/backup.log` y `logs/restore.log`
- Scripts: `scripts/backup.sh` y `scripts/restore.sh`
