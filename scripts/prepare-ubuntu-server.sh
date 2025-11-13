#!/bin/bash

################################################################################
# Script de Preparación del Servidor Ubuntu para Despliegue
# Sistema de Registro de Patrimonio DRTC Puno
#
# Este script prepara un servidor Ubuntu para el despliegue del sistema:
# - Instala Docker Engine y Docker Compose
# - Configura el firewall UFW
# - Crea usuario de despliegue
# - Configura límites del sistema
# - Valida pre-requisitos
#
# Uso: sudo ./scripts/prepare-ubuntu-server.sh [--user USERNAME] [--ssh-key PATH]
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables por defecto
DEPLOY_USER="${DEPLOY_USER:-patrimonio}"
SSH_KEY_PATH=""
LOG_FILE="/var/log/prepare-server.log"

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Función de ayuda
show_help() {
    cat << EOF
Uso: sudo $0 [OPTIONS]

Opciones:
    --user USERNAME     Nombre del usuario de despliegue (default: patrimonio)
    --ssh-key PATH      Ruta a la clave SSH pública para el usuario
    --help              Mostrar esta ayuda

Ejemplo:
    sudo $0 --user patrimonio --ssh-key ~/.ssh/id_rsa.pub

EOF
    exit 0
}

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            DEPLOY_USER="$2"
            shift 2
            ;;
        --ssh-key)
            SSH_KEY_PATH="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            error "Opción desconocida: $1. Use --help para ver opciones disponibles."
            ;;
    esac
done

# Verificar que se ejecuta como root
if [[ $EUID -ne 0 ]]; then
   error "Este script debe ejecutarse como root (use sudo)"
fi

log "=== Iniciando preparación del servidor Ubuntu ==="
log "Usuario de despliegue: $DEPLOY_USER"

################################################################################
# 1. VALIDAR PRE-REQUISITOS
################################################################################

log "Validando pre-requisitos del sistema..."

# Verificar versión de Ubuntu
if [ -f /etc/os-release ]; then
    . /etc/os-release
    log "Sistema operativo detectado: $NAME $VERSION"
    
    # Extraer versión numérica
    VERSION_ID_NUM=$(echo "$VERSION_ID" | cut -d. -f1)
    
    if [[ "$ID" != "ubuntu" ]]; then
        error "Este script está diseñado para Ubuntu. Sistema detectado: $ID"
    fi
    
    if [[ "$VERSION_ID_NUM" -lt 20 ]]; then
        error "Se requiere Ubuntu 20.04 o superior. Versión detectada: $VERSION_ID"
    fi
    
    log "✓ Versión de Ubuntu válida: $VERSION_ID"
else
    error "No se pudo detectar la versión del sistema operativo"
fi

# Verificar recursos mínimos
log "Verificando recursos del sistema..."

# CPU cores
CPU_CORES=$(nproc)
if [[ $CPU_CORES -lt 2 ]]; then
    warning "Se detectaron $CPU_CORES cores. Se recomiendan al menos 4 cores para producción."
else
    log "✓ CPU cores: $CPU_CORES"
fi

# RAM
TOTAL_RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
if [[ $TOTAL_RAM_GB -lt 4 ]]; then
    warning "Se detectaron ${TOTAL_RAM_GB}GB de RAM. Se recomiendan al menos 8GB para producción."
else
    log "✓ RAM: ${TOTAL_RAM_GB}GB"
fi

# Espacio en disco
DISK_SPACE_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [[ $DISK_SPACE_GB -lt 50 ]]; then
    warning "Espacio disponible: ${DISK_SPACE_GB}GB. Se recomiendan al menos 100GB para producción."
else
    log "✓ Espacio en disco: ${DISK_SPACE_GB}GB disponibles"
fi

################################################################################
# 2. ACTUALIZAR SISTEMA E INSTALAR DEPENDENCIAS BÁSICAS
################################################################################

log "Actualizando sistema e instalando dependencias básicas..."

export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get upgrade -y -qq

# Instalar dependencias básicas
apt-get install -y -qq \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    software-properties-common \
    wget \
    unzip \
    htop \
    net-tools

log "✓ Dependencias básicas instaladas"

################################################################################
# 3. INSTALAR DOCKER ENGINE
################################################################################

log "Instalando Docker Engine..."

# Verificar si Docker ya está instalado
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    log "Docker ya está instalado: versión $DOCKER_VERSION"
else
    # Agregar repositorio oficial de Docker
    log "Agregando repositorio de Docker..."
    
    # Eliminar versiones antiguas si existen
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Agregar GPG key de Docker
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Agregar repositorio
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Instalar Docker Engine
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    log "✓ Docker Engine instalado"
fi

# Verificar instalación de Docker
DOCKER_VERSION=$(docker --version)
log "Docker instalado: $DOCKER_VERSION"

# Iniciar y habilitar Docker
systemctl start docker
systemctl enable docker

log "✓ Docker Engine configurado y en ejecución"

################################################################################
# 4. INSTALAR DOCKER COMPOSE
################################################################################

log "Verificando Docker Compose..."

# Docker Compose v2 viene como plugin con Docker Engine
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
    log "✓ Docker Compose instalado: versión $COMPOSE_VERSION"
else
    error "Docker Compose no está disponible. Reinstale Docker Engine."
fi

################################################################################
# 5. CREAR USUARIO DE DESPLIEGUE
################################################################################

log "Configurando usuario de despliegue: $DEPLOY_USER..."

# Verificar si el usuario ya existe
if id "$DEPLOY_USER" &>/dev/null; then
    log "El usuario $DEPLOY_USER ya existe"
else
    # Crear usuario sin contraseña (se usará SSH key)
    useradd -m -s /bin/bash "$DEPLOY_USER"
    log "✓ Usuario $DEPLOY_USER creado"
fi

# Agregar usuario al grupo docker
usermod -aG docker "$DEPLOY_USER"
log "✓ Usuario $DEPLOY_USER agregado al grupo docker"

# Agregar usuario al grupo sudo
usermod -aG sudo "$DEPLOY_USER"
log "✓ Usuario $DEPLOY_USER agregado al grupo sudo"

# Configurar sudo sin contraseña para el usuario
echo "$DEPLOY_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$DEPLOY_USER
chmod 0440 /etc/sudoers.d/$DEPLOY_USER
log "✓ Sudo sin contraseña configurado para $DEPLOY_USER"

# Configurar SSH key si se proporcionó
if [[ -n "$SSH_KEY_PATH" ]]; then
    if [[ -f "$SSH_KEY_PATH" ]]; then
        USER_HOME=$(eval echo ~$DEPLOY_USER)
        mkdir -p "$USER_HOME/.ssh"
        cat "$SSH_KEY_PATH" >> "$USER_HOME/.ssh/authorized_keys"
        chmod 700 "$USER_HOME/.ssh"
        chmod 600 "$USER_HOME/.ssh/authorized_keys"
        chown -R "$DEPLOY_USER:$DEPLOY_USER" "$USER_HOME/.ssh"
        log "✓ SSH key configurada para $DEPLOY_USER"
    else
        warning "SSH key no encontrada en: $SSH_KEY_PATH"
    fi
fi

################################################################################
# 6. CONFIGURAR FIREWALL UFW
################################################################################

log "Configurando firewall UFW..."

# Habilitar UFW si no está activo
if ! ufw status | grep -q "Status: active"; then
    # Configurar reglas antes de habilitar
    ufw --force reset
    
    # Permitir SSH (puerto 22) - IMPORTANTE: hacer esto primero
    ufw allow 22/tcp comment 'SSH'
    log "✓ Regla UFW: Puerto 22 (SSH) permitido"
    
    # Permitir HTTP (puerto 80)
    ufw allow 80/tcp comment 'HTTP'
    log "✓ Regla UFW: Puerto 80 (HTTP) permitido"
    
    # Permitir HTTPS (puerto 443)
    ufw allow 443/tcp comment 'HTTPS'
    log "✓ Regla UFW: Puerto 443 (HTTPS) permitido"
    
    # Habilitar UFW
    ufw --force enable
    log "✓ UFW habilitado"
else
    log "UFW ya está activo"
    
    # Asegurar que las reglas necesarias existen
    ufw allow 22/tcp comment 'SSH' 2>/dev/null || true
    ufw allow 80/tcp comment 'HTTP' 2>/dev/null || true
    ufw allow 443/tcp comment 'HTTPS' 2>/dev/null || true
    
    log "✓ Reglas UFW verificadas"
fi

# Mostrar estado del firewall
log "Estado del firewall:"
ufw status numbered | tee -a "$LOG_FILE"

################################################################################
# 7. CONFIGURAR LÍMITES DEL SISTEMA
################################################################################

log "Configurando límites del sistema..."

# Configurar límites en /etc/security/limits.conf
LIMITS_FILE="/etc/security/limits.conf"

# Backup del archivo original
if [[ ! -f "${LIMITS_FILE}.backup" ]]; then
    cp "$LIMITS_FILE" "${LIMITS_FILE}.backup"
fi

# Agregar límites si no existen
if ! grep -q "# Patrimonio System Limits" "$LIMITS_FILE"; then
    cat >> "$LIMITS_FILE" << EOF

# Patrimonio System Limits
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
$DEPLOY_USER soft nofile 65536
$DEPLOY_USER hard nofile 65536
$DEPLOY_USER soft nproc 32768
$DEPLOY_USER hard nproc 32768
EOF
    log "✓ Límites de archivos y procesos configurados"
else
    log "Límites del sistema ya configurados"
fi

# Configurar límites del kernel
SYSCTL_FILE="/etc/sysctl.d/99-patrimonio.conf"

cat > "$SYSCTL_FILE" << EOF
# Patrimonio System Kernel Parameters

# Aumentar límites de archivos
fs.file-max = 2097152

# Optimizaciones de red
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.core.netdev_max_backlog = 5000

# Optimizaciones de memoria
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 2

# Seguridad
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
EOF

# Aplicar configuración
sysctl -p "$SYSCTL_FILE" > /dev/null 2>&1

log "✓ Parámetros del kernel configurados"

################################################################################
# 8. CONFIGURAR DOCKER DAEMON
################################################################################

log "Configurando Docker daemon..."

DOCKER_DAEMON_FILE="/etc/docker/daemon.json"

# Crear configuración de Docker daemon
cat > "$DOCKER_DAEMON_FILE" << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "userland-proxy": false,
  "live-restore": true
}
EOF

# Reiniciar Docker para aplicar cambios
systemctl restart docker

log "✓ Docker daemon configurado"

################################################################################
# 9. CREAR DIRECTORIOS DE TRABAJO
################################################################################

log "Creando estructura de directorios..."

USER_HOME=$(eval echo ~$DEPLOY_USER)

# Crear directorios necesarios
mkdir -p "$USER_HOME/patrimonio"
mkdir -p "$USER_HOME/backups/db"
mkdir -p "$USER_HOME/backups/media"
mkdir -p "/var/lib/docker/volumes/patrimonio_postgres"
mkdir -p "/var/lib/docker/volumes/patrimonio_redis"
mkdir -p "/var/lib/docker/volumes/patrimonio_media"
mkdir -p "/var/lib/docker/volumes/patrimonio_static"

# Establecer permisos
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$USER_HOME/patrimonio"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$USER_HOME/backups"

log "✓ Estructura de directorios creada"

################################################################################
# 10. VERIFICACIÓN FINAL
################################################################################

log "Ejecutando verificaciones finales..."

# Verificar Docker
if docker run --rm hello-world > /dev/null 2>&1; then
    log "✓ Docker funcionando correctamente"
else
    error "Docker no está funcionando correctamente"
fi

# Verificar Docker Compose
if docker compose version > /dev/null 2>&1; then
    log "✓ Docker Compose funcionando correctamente"
else
    error "Docker Compose no está funcionando correctamente"
fi

# Verificar UFW
if ufw status | grep -q "Status: active"; then
    log "✓ UFW activo y configurado"
else
    warning "UFW no está activo"
fi

# Verificar usuario puede usar Docker
if sudo -u "$DEPLOY_USER" docker ps > /dev/null 2>&1; then
    log "✓ Usuario $DEPLOY_USER puede usar Docker"
else
    warning "Usuario $DEPLOY_USER no puede usar Docker. Puede requerir logout/login."
fi

################################################################################
# RESUMEN
################################################################################

log ""
log "=========================================="
log "  PREPARACIÓN DEL SERVIDOR COMPLETADA"
log "=========================================="
log ""
log "Resumen de la configuración:"
log "  - Sistema: $NAME $VERSION"
log "  - Docker: $(docker --version | awk '{print $3}' | sed 's/,//')"
log "  - Docker Compose: $(docker compose version | awk '{print $4}')"
log "  - Usuario de despliegue: $DEPLOY_USER"
log "  - Firewall UFW: Activo (puertos 22, 80, 443)"
log "  - Límites del sistema: Configurados"
log ""
log "Próximos pasos:"
log "  1. Cerrar sesión y volver a iniciar como $DEPLOY_USER"
log "  2. Clonar el repositorio del proyecto"
log "  3. Ejecutar: ./scripts/configure-env.sh"
log "  4. Ejecutar: ./scripts/deploy-ubuntu.sh"
log ""
log "Log completo guardado en: $LOG_FILE"
log ""

exit 0
