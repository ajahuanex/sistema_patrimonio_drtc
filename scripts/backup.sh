#!/bin/bash

################################################################################
# Sistema de Backups Automáticos - Sistema de Registro de Patrimonio DRTC Puno
# 
# Este script realiza backups automáticos de:
# - Base de datos PostgreSQL (pg_dump con compresión gzip)
# - Archivos media (tar.gz)
# - Limpieza automática de backups antiguos (>7 días)
# - Logging de resultados
# - Notificación por email en caso de fallo
################################################################################

set -e
set -u
set -o pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups"
DB_BACKUP_DIR="${BACKUP_DIR}/db"
MEDIA_BACKUP_DIR="${BACKUP_DIR}/media"
LOG_DIR="${PROJECT_ROOT}/logs"
BACKUP_LOG="${LOG_DIR}/backup.log"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Variables de entorno (se cargan desde .env.prod)
ENV_FILE="${PROJECT_ROOT}/.env.prod"

# Función para logging
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${BACKUP_LOG}"
}

log_info() {
    log "INFO" "${GREEN}$@${NC}"
}

log_warn() {
    log "WARN" "${YELLOW}$@${NC}"
}

log_error() {
    log "ERROR" "${RED}$@${NC}"
}

# Función para enviar notificación por email
send_email_notification() {
    local subject="$1"
    local body="$2"
    
    if [ -z "${EMAIL_HOST_USER:-}" ] || [ -z "${EMAIL_HOST_PASSWORD:-}" ]; then
        log_warn "Email no configurado, saltando notificación"
        return 0
    fi
    
    # Usar el contenedor web para enviar email via Django
    docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" exec -T web python manage.py shell <<EOF
from django.core.mail import send_mail
from django.conf import settings

try:
    send_mail(
        subject='${subject}',
        message='''${body}''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else [settings.EMAIL_HOST_USER],
        fail_silently=False
    )
    print("Email enviado exitosamente")
except Exception as e:
    print(f"Error enviando email: {e}")
EOF
}

# Función para crear estructura de directorios
create_backup_directories() {
    log_info "Creando estructura de directorios de backup..."
    
    mkdir -p "${DB_BACKUP_DIR}"
    mkdir -p "${MEDIA_BACKUP_DIR}"
    mkdir -p "${LOG_DIR}"
    
    log_info "Directorios creados: ${DB_BACKUP_DIR}, ${MEDIA_BACKUP_DIR}"
}

# Función para cargar variables de entorno
load_environment() {
    if [ ! -f "${ENV_FILE}" ]; then
        log_error "Archivo .env.prod no encontrado en ${ENV_FILE}"
        exit 1
    fi
    
    log_info "Cargando variables de entorno desde ${ENV_FILE}"
    set -a
    source "${ENV_FILE}"
    set +a
}

# Función para verificar que Docker está corriendo
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker no está corriendo o no tienes permisos"
        exit 1
    fi
    
    log_info "Docker está corriendo correctamente"
}

# Función para verificar que los servicios están activos
check_services() {
    log_info "Verificando servicios Docker..."
    
    if ! docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" ps | grep -q "db.*Up"; then
        log_error "Servicio de base de datos no está corriendo"
        exit 1
    fi
    
    log_info "Servicios verificados correctamente"
}

# Función para realizar backup de PostgreSQL
backup_database() {
    log_info "Iniciando backup de base de datos PostgreSQL..."
    
    local backup_file="${DB_BACKUP_DIR}/patrimonio_${TIMESTAMP}.sql"
    local backup_file_gz="${backup_file}.gz"
    
    # Realizar pg_dump
    if docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" exec -T db \
        pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "${backup_file}"; then
        
        log_info "Dump de base de datos completado: ${backup_file}"
        
        # Comprimir con gzip
        if gzip "${backup_file}"; then
            local size=$(du -h "${backup_file_gz}" | cut -f1)
            log_info "Backup comprimido exitosamente: ${backup_file_gz} (${size})"
            return 0
        else
            log_error "Error al comprimir backup de base de datos"
            return 1
        fi
    else
        log_error "Error al realizar dump de base de datos"
        return 1
    fi
}

# Función para realizar backup de archivos media
backup_media() {
    log_info "Iniciando backup de archivos media..."
    
    local media_source="${PROJECT_ROOT}/media"
    local backup_file="${MEDIA_BACKUP_DIR}/media_${TIMESTAMP}.tar.gz"
    
    # Verificar si existe el directorio media
    if [ ! -d "${media_source}" ]; then
        log_warn "Directorio media no encontrado en ${media_source}, saltando backup de media"
        return 0
    fi
    
    # Verificar si hay archivos en media
    if [ -z "$(ls -A ${media_source})" ]; then
        log_warn "Directorio media está vacío, saltando backup"
        return 0
    fi
    
    # Crear archivo tar.gz
    if tar -czf "${backup_file}" -C "${PROJECT_ROOT}" media/; then
        local size=$(du -h "${backup_file}" | cut -f1)
        log_info "Backup de media completado: ${backup_file} (${size})"
        return 0
    else
        log_error "Error al crear backup de archivos media"
        return 1
    fi
}

# Función para limpiar backups antiguos
cleanup_old_backups() {
    log_info "Limpiando backups antiguos (más de ${RETENTION_DAYS} días)..."
    
    local deleted_count=0
    
    # Limpiar backups de base de datos
    if [ -d "${DB_BACKUP_DIR}" ]; then
        while IFS= read -r -d '' file; do
            log_info "Eliminando backup antiguo: $(basename "$file")"
            rm -f "$file"
            ((deleted_count++))
        done < <(find "${DB_BACKUP_DIR}" -name "*.sql.gz" -type f -mtime +${RETENTION_DAYS} -print0)
    fi
    
    # Limpiar backups de media
    if [ -d "${MEDIA_BACKUP_DIR}" ]; then
        while IFS= read -r -d '' file; do
            log_info "Eliminando backup antiguo: $(basename "$file")"
            rm -f "$file"
            ((deleted_count++))
        done < <(find "${MEDIA_BACKUP_DIR}" -name "*.tar.gz" -type f -mtime +${RETENTION_DAYS} -print0)
    fi
    
    if [ ${deleted_count} -eq 0 ]; then
        log_info "No hay backups antiguos para eliminar"
    else
        log_info "Se eliminaron ${deleted_count} backups antiguos"
    fi
}

# Función para mostrar estadísticas de backups
show_backup_stats() {
    log_info "=== Estadísticas de Backups ==="
    
    if [ -d "${DB_BACKUP_DIR}" ]; then
        local db_count=$(find "${DB_BACKUP_DIR}" -name "*.sql.gz" -type f | wc -l)
        local db_size=$(du -sh "${DB_BACKUP_DIR}" 2>/dev/null | cut -f1)
        log_info "Backups de base de datos: ${db_count} archivos, ${db_size}"
    fi
    
    if [ -d "${MEDIA_BACKUP_DIR}" ]; then
        local media_count=$(find "${MEDIA_BACKUP_DIR}" -name "*.tar.gz" -type f | wc -l)
        local media_size=$(du -sh "${MEDIA_BACKUP_DIR}" 2>/dev/null | cut -f1)
        log_info "Backups de media: ${media_count} archivos, ${media_size}"
    fi
    
    log_info "================================"
}

# Función principal
main() {
    local start_time=$(date +%s)
    local backup_success=true
    local error_messages=""
    
    log_info "=========================================="
    log_info "Iniciando proceso de backup - ${TIMESTAMP}"
    log_info "=========================================="
    
    # Crear directorios
    create_backup_directories
    
    # Cargar variables de entorno
    load_environment
    
    # Verificar Docker
    check_docker
    
    # Verificar servicios
    check_services
    
    # Realizar backup de base de datos
    if ! backup_database; then
        backup_success=false
        error_messages="${error_messages}\n- Error en backup de base de datos"
    fi
    
    # Realizar backup de archivos media
    if ! backup_media; then
        backup_success=false
        error_messages="${error_messages}\n- Error en backup de archivos media"
    fi
    
    # Limpiar backups antiguos
    cleanup_old_backups
    
    # Mostrar estadísticas
    show_backup_stats
    
    # Calcular tiempo de ejecución
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_info "Tiempo de ejecución: ${duration} segundos"
    
    # Resultado final
    if [ "$backup_success" = true ]; then
        log_info "=========================================="
        log_info "Backup completado exitosamente"
        log_info "=========================================="
        exit 0
    else
        log_error "=========================================="
        log_error "Backup completado con errores:"
        echo -e "${error_messages}" | tee -a "${BACKUP_LOG}"
        log_error "=========================================="
        
        # Enviar notificación por email
        send_email_notification \
            "[CRÍTICO] Fallo en Backup - Sistema Patrimonio" \
            "El proceso de backup falló con los siguientes errores:${error_messages}\n\nTimestamp: ${TIMESTAMP}\nServidor: $(hostname)\n\nPor favor, revise los logs en: ${BACKUP_LOG}"
        
        exit 1
    fi
}

# Manejo de señales
trap 'log_error "Script interrumpido por señal"; exit 130' INT TERM

# Ejecutar función principal
main "$@"
