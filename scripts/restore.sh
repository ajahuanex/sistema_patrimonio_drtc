#!/bin/bash

################################################################################
# Script de Restauración de Backups - Sistema de Registro de Patrimonio DRTC Puno
# 
# Este script restaura backups de:
# - Base de datos PostgreSQL desde archivos .sql.gz
# - Archivos media desde archivos .tar.gz
################################################################################

set -e
set -u
set -o pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups"
DB_BACKUP_DIR="${BACKUP_DIR}/db"
MEDIA_BACKUP_DIR="${BACKUP_DIR}/media"
LOG_DIR="${PROJECT_ROOT}/logs"
RESTORE_LOG="${LOG_DIR}/restore.log"

# Variables de entorno
ENV_FILE="${PROJECT_ROOT}/.env.prod"

# Función para logging
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${RESTORE_LOG}"
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

# Función para mostrar uso
show_usage() {
    echo -e "${BLUE}Uso:${NC}"
    echo "  $0 --db BACKUP_FILE          # Restaurar solo base de datos"
    echo "  $0 --media BACKUP_FILE       # Restaurar solo archivos media"
    echo "  $0 --db BACKUP_FILE --media BACKUP_FILE  # Restaurar ambos"
    echo "  $0 --list                    # Listar backups disponibles"
    echo ""
    echo -e "${BLUE}Ejemplos:${NC}"
    echo "  $0 --db patrimonio_20241112_030000.sql.gz"
    echo "  $0 --media media_20241112_030000.tar.gz"
    echo "  $0 --list"
    exit 1
}

# Función para listar backups disponibles
list_backups() {
    log_info "=== Backups Disponibles ==="
    
    if [ -d "${DB_BACKUP_DIR}" ]; then
        echo -e "\n${BLUE}Backups de Base de Datos:${NC}"
        ls -lh "${DB_BACKUP_DIR}"/*.sql.gz 2>/dev/null | awk '{print $9, "(" $5 ")", $6, $7, $8}' || echo "No hay backups de base de datos"
    fi
    
    if [ -d "${MEDIA_BACKUP_DIR}" ]; then
        echo -e "\n${BLUE}Backups de Media:${NC}"
        ls -lh "${MEDIA_BACKUP_DIR}"/*.tar.gz 2>/dev/null | awk '{print $9, "(" $5 ")", $6, $7, $8}' || echo "No hay backups de media"
    fi
    
    echo ""
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

# Función para verificar Docker
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker no está corriendo o no tienes permisos"
        exit 1
    fi
    
    log_info "Docker está corriendo correctamente"
}

# Función para verificar servicios
check_services() {
    log_info "Verificando servicios Docker..."
    
    if ! docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" ps | grep -q "db.*Up"; then
        log_error "Servicio de base de datos no está corriendo"
        log_error "Inicie los servicios con: docker-compose -f docker-compose.prod.yml up -d"
        exit 1
    fi
    
    log_info "Servicios verificados correctamente"
}

# Función para confirmar acción
confirm_action() {
    local message="$1"
    echo -e "${YELLOW}${message}${NC}"
    read -p "¿Está seguro? (escriba 'SI' para confirmar): " confirmation
    
    if [ "$confirmation" != "SI" ]; then
        log_warn "Operación cancelada por el usuario"
        exit 0
    fi
}

# Función para restaurar base de datos
restore_database() {
    local backup_file="$1"
    local backup_path
    
    # Verificar si es ruta completa o solo nombre de archivo
    if [ -f "${backup_file}" ]; then
        backup_path="${backup_file}"
    elif [ -f "${DB_BACKUP_DIR}/${backup_file}" ]; then
        backup_path="${DB_BACKUP_DIR}/${backup_file}"
    else
        log_error "Archivo de backup no encontrado: ${backup_file}"
        exit 1
    fi
    
    log_info "Restaurando base de datos desde: ${backup_path}"
    
    # Confirmar acción
    confirm_action "ADVERTENCIA: Esta operación sobrescribirá la base de datos actual."
    
    # Crear backup de seguridad antes de restaurar
    local safety_backup="${DB_BACKUP_DIR}/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
    log_info "Creando backup de seguridad en: ${safety_backup}"
    
    docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" exec -T db \
        pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${safety_backup}"
    
    # Descomprimir y restaurar
    log_info "Descomprimiendo y restaurando backup..."
    
    if gunzip -c "${backup_path}" | docker-compose -f "${PROJECT_ROOT}/docker-compose.prod.yml" exec -T db \
        psql -U "${POSTGRES_USER}" "${POSTGRES_DB}"; then
        log_info "Base de datos restaurada exitosamente"
        log_info "Backup de seguridad guardado en: ${safety_backup}"
        return 0
    else
        log_error "Error al restaurar base de datos"
        log_error "Puede restaurar el backup de seguridad desde: ${safety_backup}"
        return 1
    fi
}

# Función para restaurar archivos media
restore_media() {
    local backup_file="$1"
    local backup_path
    
    # Verificar si es ruta completa o solo nombre de archivo
    if [ -f "${backup_file}" ]; then
        backup_path="${backup_file}"
    elif [ -f "${MEDIA_BACKUP_DIR}/${backup_file}" ]; then
        backup_path="${MEDIA_BACKUP_DIR}/${backup_file}"
    else
        log_error "Archivo de backup no encontrado: ${backup_file}"
        exit 1
    fi
    
    log_info "Restaurando archivos media desde: ${backup_path}"
    
    # Confirmar acción
    confirm_action "ADVERTENCIA: Esta operación sobrescribirá los archivos media actuales."
    
    # Crear backup de seguridad antes de restaurar
    local safety_backup="${MEDIA_BACKUP_DIR}/pre_restore_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    if [ -d "${PROJECT_ROOT}/media" ] && [ "$(ls -A ${PROJECT_ROOT}/media)" ]; then
        log_info "Creando backup de seguridad en: ${safety_backup}"
        tar -czf "${safety_backup}" -C "${PROJECT_ROOT}" media/
    fi
    
    # Restaurar archivos media
    log_info "Extrayendo archivos media..."
    
    if tar -xzf "${backup_path}" -C "${PROJECT_ROOT}"; then
        log_info "Archivos media restaurados exitosamente"
        if [ -f "${safety_backup}" ]; then
            log_info "Backup de seguridad guardado en: ${safety_backup}"
        fi
        return 0
    else
        log_error "Error al restaurar archivos media"
        if [ -f "${safety_backup}" ]; then
            log_error "Puede restaurar el backup de seguridad desde: ${safety_backup}"
        fi
        return 1
    fi
}

# Función principal
main() {
    local db_backup=""
    local media_backup=""
    local list_only=false
    
    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --db)
                db_backup="$2"
                shift 2
                ;;
            --media)
                media_backup="$2"
                shift 2
                ;;
            --list)
                list_only=true
                shift
                ;;
            -h|--help)
                show_usage
                ;;
            *)
                log_error "Argumento desconocido: $1"
                show_usage
                ;;
        esac
    done
    
    # Crear directorio de logs
    mkdir -p "${LOG_DIR}"
    
    log_info "=========================================="
    log_info "Script de Restauración de Backups"
    log_info "=========================================="
    
    # Si solo se solicita listar
    if [ "$list_only" = true ]; then
        list_backups
        exit 0
    fi
    
    # Verificar que se especificó al menos un backup
    if [ -z "$db_backup" ] && [ -z "$media_backup" ]; then
        log_error "Debe especificar al menos un backup para restaurar"
        show_usage
    fi
    
    # Cargar variables de entorno
    load_environment
    
    # Verificar Docker
    check_docker
    
    # Verificar servicios
    check_services
    
    local restore_success=true
    
    # Restaurar base de datos si se especificó
    if [ -n "$db_backup" ]; then
        if ! restore_database "$db_backup"; then
            restore_success=false
        fi
    fi
    
    # Restaurar media si se especificó
    if [ -n "$media_backup" ]; then
        if ! restore_media "$media_backup"; then
            restore_success=false
        fi
    fi
    
    # Resultado final
    if [ "$restore_success" = true ]; then
        log_info "=========================================="
        log_info "Restauración completada exitosamente"
        log_info "=========================================="
        exit 0
    else
        log_error "=========================================="
        log_error "Restauración completada con errores"
        log_error "=========================================="
        exit 1
    fi
}

# Manejo de señales
trap 'log_error "Script interrumpido por señal"; exit 130' INT TERM

# Ejecutar función principal
main "$@"
