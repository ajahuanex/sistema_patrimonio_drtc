# Guía de Instalación - Sistema de Registro de Patrimonio

## Requisitos del Sistema

### Hardware Mínimo
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Almacenamiento**: 50 GB SSD
- **Red**: Conexión a internet estable

### Hardware Recomendado
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Almacenamiento**: 100+ GB SSD
- **Red**: Conexión a internet de alta velocidad

### Software Requerido
- **Sistema Operativo**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.25+

## Instalación en Linux (Ubuntu/CentOS)

### 1. Preparación del Sistema

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y  # Ubuntu
sudo yum update -y                      # CentOS

# Instalar dependencias básicas
sudo apt install -y curl wget git unzip  # Ubuntu
sudo yum install -y curl wget git unzip  # CentOS
```

### 2. Instalar Docker y Docker Compose

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalación
docker --version
docker-compose --version
```

### 3. Clonar el Repositorio

```bash
# Clonar el proyecto
git clone https://github.com/tu-organizacion/sistema-patrimonio.git
cd sistema-patrimonio

# Crear directorios necesarios
mkdir -p logs backups nginx/logs certbot/conf certbot/www
```

### 4. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.prod.example .env.prod

# Editar configuración
nano .env.prod
```

**Configurar las siguientes variables:**

```env
# Django Settings
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria-aqui
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Database
POSTGRES_DB=patrimonio_prod
POSTGRES_USER=patrimonio_user
POSTGRES_PASSWORD=tu-password-seguro-de-base-de-datos

# Redis
REDIS_PASSWORD=tu-password-seguro-de-redis

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-de-aplicacion

# Domain
BASE_URL=https://tu-dominio.com
```

### 5. Desplegar la Aplicación

```bash
# Hacer ejecutables los scripts
chmod +x scripts/*.sh

# Ejecutar despliegue
./scripts/deploy.sh tu-dominio.com tu-email@gmail.com production
```

### 6. Configurar SSL (Let's Encrypt)

```bash
# El script de despliegue configurará SSL automáticamente
# Si necesitas configurarlo manualmente:
./scripts/setup-ssl.sh tu-dominio.com tu-email@gmail.com
```

## Instalación en Windows

### 1. Preparación del Sistema

1. Instalar **Docker Desktop for Windows**
2. Instalar **Git for Windows**
3. Habilitar **WSL2** (recomendado)

### 2. Clonar y Configurar

```cmd
# Clonar el proyecto
git clone https://github.com/tu-organizacion/sistema-patrimonio.git
cd sistema-patrimonio

# Crear directorios
mkdir logs backups nginx\logs certbot\conf certbot\www

# Copiar configuración
copy .env.prod.example .env.prod
```

### 3. Configurar Variables de Entorno

Editar `.env.prod` con los valores apropiados (ver sección Linux).

### 4. Desplegar

```cmd
# Ejecutar despliegue
scripts\deploy.bat tu-dominio.com tu-email@gmail.com production
```

## Configuración Post-Instalación

### 1. Acceder al Sistema

- **Aplicación Web**: `https://tu-dominio.com`
- **Panel Admin**: `https://tu-dominio.com/admin/`
- **API**: `https://tu-dominio.com/api/`

### 2. Cambiar Credenciales por Defecto

```bash
# Acceder al contenedor web
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# En el shell de Django:
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')
admin.set_password('tu-nuevo-password-seguro')
admin.email = 'tu-email@dominio.com'
admin.save()
```

### 3. Configurar Permisos de Usuario

1. Acceder al panel admin: `https://tu-dominio.com/admin/`
2. Ir a **Core > Usuarios**
3. Crear usuarios adicionales con roles apropiados
4. Configurar grupos y permisos según necesidades

### 4. Importar Datos Iniciales

```bash
# Importar catálogo oficial
# Acceder a: https://tu-dominio.com/catalogo/importar/
# Subir archivo Excel con catálogo SBN

# Importar oficinas
# Acceder a: https://tu-dominio.com/oficinas/importar/
# Subir archivo Excel con oficinas

# Importar inventario existente (opcional)
# Acceder a: https://tu-dominio.com/bienes/importar/
# Subir archivo Excel con inventario actual
```

## Verificación de la Instalación

### 1. Health Check

```bash
# Verificar estado de la aplicación
curl https://tu-dominio.com/health/

# Verificar estado detallado
curl https://tu-dominio.com/health/detailed/
```

### 2. Verificar Servicios

```bash
# Ver estado de contenedores
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. Pruebas Funcionales

1. **Registro de Bien**: Crear un bien patrimonial de prueba
2. **Generación QR**: Verificar que se genere código QR
3. **Escaneo Móvil**: Probar acceso desde dispositivo móvil
4. **Reportes**: Generar un reporte de prueba
5. **Backup**: Ejecutar backup manual

## Solución de Problemas Comunes

### Error de Conexión a Base de Datos

```bash
# Verificar estado de PostgreSQL
docker-compose -f docker-compose.prod.yml logs db

# Reiniciar base de datos
docker-compose -f docker-compose.prod.yml restart db
```

### Error de SSL

```bash
# Verificar certificados
ls -la certbot/conf/live/tu-dominio.com/

# Renovar certificados
docker-compose -f docker-compose.prod.yml run --rm certbot renew
```

### Error de Permisos

```bash
# Verificar permisos de archivos
ls -la logs/ backups/

# Corregir permisos
sudo chown -R $USER:$USER logs/ backups/
```

### Contenedores No Inician

```bash
# Ver logs detallados
docker-compose -f docker-compose.prod.yml logs

# Reconstruir imágenes
docker-compose -f docker-compose.prod.yml build --no-cache

# Limpiar volúmenes (CUIDADO: elimina datos)
docker-compose -f docker-compose.prod.yml down -v
```

## Configuración de Firewall

### Ubuntu (UFW)

```bash
# Habilitar firewall
sudo ufw enable

# Permitir SSH
sudo ufw allow ssh

# Permitir HTTP y HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Ver estado
sudo ufw status
```

### CentOS (firewalld)

```bash
# Habilitar servicios
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh

# Recargar configuración
sudo firewall-cmd --reload
```

## Configuración de Dominio

### DNS Records

Configurar los siguientes registros DNS:

```
A     tu-dominio.com        IP-DEL-SERVIDOR
A     www.tu-dominio.com    IP-DEL-SERVIDOR
CNAME api.tu-dominio.com    tu-dominio.com
```

### Verificación DNS

```bash
# Verificar resolución DNS
nslookup tu-dominio.com
dig tu-dominio.com
```

## Monitoreo y Alertas

### Configurar Monitoreo Automático

```bash
# Agregar script de monitoreo al cron
crontab -e

# Agregar línea:
*/5 * * * * /ruta/al/proyecto/scripts/monitor.sh
```

### Configurar Alertas por Email

Editar `scripts/monitor.sh` y configurar:

```bash
ALERT_EMAIL="admin@tu-dominio.com"
```

## Actualizaciones

### Actualizar la Aplicación

```bash
# Hacer backup antes de actualizar
./scripts/backup.sh

# Obtener última versión
git pull origin main

# Reconstruir y desplegar
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Ejecutar migraciones
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Actualizar Docker Images

```bash
# Actualizar imágenes base
docker-compose -f docker-compose.prod.yml pull

# Reconstruir aplicación
docker-compose -f docker-compose.prod.yml build --no-cache
```

## Contacto y Soporte

Para soporte técnico, contactar a:
- **Email**: soporte@tu-dominio.com
- **Documentación**: https://tu-dominio.com/docs/
- **Issues**: https://github.com/tu-organizacion/sistema-patrimonio/issues