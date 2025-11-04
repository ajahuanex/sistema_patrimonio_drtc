#!/bin/bash

# Backup Script for Sistema de Registro de Patrimonio
# This script creates backups of database and media files

set -e

# Configuration
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Load environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | grep -v '^#' | xargs)
fi

echo "Starting backup process..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Creating database backup..."
docker-compose -f docker-compose.prod.yml exec -T db pg_dump \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists > $BACKUP_DIR/db_backup_$DATE.sql

# Compress database backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
echo "Creating media files backup..."
docker run --rm \
    -v patrimonio_media_files:/data \
    -v $(pwd)/$BACKUP_DIR:/backup \
    alpine tar czf /backup/media_backup_$DATE.tar.gz -C /data .

# Static files backup (optional)
echo "Creating static files backup..."
docker run --rm \
    -v patrimonio_static_files:/data \
    -v $(pwd)/$BACKUP_DIR:/backup \
    alpine tar czf /backup/static_backup_$DATE.tar.gz -C /data .

# Configuration backup
echo "Creating configuration backup..."
tar czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
    docker-compose.prod.yml \
    nginx/ \
    .env.prod \
    scripts/ \
    --exclude=scripts/logs

# Clean old backups
echo "Cleaning old backups (older than $RETENTION_DAYS days)..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Upload to S3 (if configured)
if [ ! -z "$AWS_ACCESS_KEY_ID" ] && [ ! -z "$BACKUP_S3_BUCKET" ]; then
    echo "Uploading backups to S3..."
    
    # Install AWS CLI if not present
    if ! command -v aws &> /dev/null; then
        echo "Installing AWS CLI..."
        pip install awscli
    fi
    
    # Upload files
    aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz s3://$BACKUP_S3_BUCKET/database/
    aws s3 cp $BACKUP_DIR/media_backup_$DATE.tar.gz s3://$BACKUP_S3_BUCKET/media/
    aws s3 cp $BACKUP_DIR/config_backup_$DATE.tar.gz s3://$BACKUP_S3_BUCKET/config/
    
    echo "Backups uploaded to S3"
fi

# Generate backup report
echo "Generating backup report..."
cat > $BACKUP_DIR/backup_report_$DATE.txt << EOF
Backup Report - $DATE
=====================

Database Backup: db_backup_$DATE.sql.gz
Size: $(du -h $BACKUP_DIR/db_backup_$DATE.sql.gz | cut -f1)

Media Backup: media_backup_$DATE.tar.gz
Size: $(du -h $BACKUP_DIR/media_backup_$DATE.tar.gz | cut -f1)

Static Backup: static_backup_$DATE.tar.gz
Size: $(du -h $BACKUP_DIR/static_backup_$DATE.tar.gz | cut -f1)

Config Backup: config_backup_$DATE.tar.gz
Size: $(du -h $BACKUP_DIR/config_backup_$DATE.tar.gz | cut -f1)

Total Backup Size: $(du -sh $BACKUP_DIR | cut -f1)

Backup completed at: $(date)
EOF

echo "Backup completed successfully!"
echo "Backup files created:"
ls -la $BACKUP_DIR/*_$DATE.*