#!/bin/bash

# Restore Script for Sistema de Registro de Patrimonio
# This script restores backups of database and media files

set -e

# Configuration
BACKUP_DIR="./backups"
BACKUP_DATE=${1}

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    ls -la $BACKUP_DIR/db_backup_*.sql.gz | sed 's/.*db_backup_\(.*\)\.sql\.gz/\1/'
    exit 1
fi

# Load environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | grep -v '^#' | xargs)
fi

echo "Starting restore process for backup: $BACKUP_DATE"

# Verify backup files exist
DB_BACKUP="$BACKUP_DIR/db_backup_$BACKUP_DATE.sql.gz"
MEDIA_BACKUP="$BACKUP_DIR/media_backup_$BACKUP_DATE.tar.gz"

if [ ! -f "$DB_BACKUP" ]; then
    echo "Error: Database backup file not found: $DB_BACKUP"
    exit 1
fi

if [ ! -f "$MEDIA_BACKUP" ]; then
    echo "Error: Media backup file not found: $MEDIA_BACKUP"
    exit 1
fi

# Confirmation
read -p "This will overwrite the current database and media files. Are you sure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 1
fi

# Stop application services
echo "Stopping application services..."
docker-compose -f docker-compose.prod.yml stop web celery celery-beat

# Restore database
echo "Restoring database..."
gunzip -c $DB_BACKUP | docker-compose -f docker-compose.prod.yml exec -T db psql \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB

# Restore media files
echo "Restoring media files..."
docker run --rm \
    -v patrimonio_media_files:/data \
    -v $(pwd)/$BACKUP_DIR:/backup \
    alpine sh -c "rm -rf /data/* && tar xzf /backup/media_backup_$BACKUP_DATE.tar.gz -C /data"

# Restart application services
echo "Restarting application services..."
docker-compose -f docker-compose.prod.yml start web celery celery-beat

# Run migrations (in case of schema changes)
echo "Running migrations..."
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
echo "Collecting static files..."
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

echo "Restore completed successfully!"
echo "Database and media files have been restored from backup: $BACKUP_DATE"