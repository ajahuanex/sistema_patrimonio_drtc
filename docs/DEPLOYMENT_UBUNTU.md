# Guía de Despliegue en Ubuntu - Sistema de Patrimonio DRTC Puno

Esta guía proporciona instrucciones detalladas para desplegar el Sistema de Registro de Patrimonio DRTC Puno en un servidor Ubuntu de producción.

## Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Preparación del Servidor](#preparación-del-servidor)
3. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
4. [Despliegue del Sistema](#despliegue-del-sistema)
5. [Verificación Post-Despliegue](#verificación-post-despliegue)
6. [Comandos Útiles](#comandos-útiles)
7. [Troubleshooting](#troubleshooting)
8. [Actualización del Sistema](#actualización-del-sistema)
9. [Rollback](#rollback)

## Requisitos Previos

### Servidor

- **Sistema Operativo**: Ubuntu 20.04 LTS o superior
- **CPU**: Mínimo 4 cores
- **RAM**: Mínimo 8 GB
- **Almacenamiento**: Mínimo 100 GB SSD
- **Red**: IP pública estática
- **Acceso**: SSH con permisos sudo

### Dominio

- Dominio registrado apuntando a la IP del servidor
- Registros DNS configurados:
  - `A` record: `dominio.com` → IP del servidor
  - `A` record: `www.dominio.com` → IP del servidor (opcional)

### Acceso

- Acceso SSH al servidor
- Usuario con permisos sudo
- Clave SSH configurada (recomendado)

## Preparación del Servidor

### Paso 1: Conectarse al Servidor

```bash
ssh usuario@ip-del-servidor
```

### Paso 2: Clonar el Repositorio

```bash
# Opción A: Si el repositorio es público
git clone https://github.com/tu-organizacion/patrimonio-drtc.git
cd patrimonio-drtc

# Opción B: Si el repositorio es privado (con SSH)
git clone git@github.com:tu-organizacion/patrimonio-drtc.git
cd patrimonio-drtc
```

### Paso 3: Ejecutar Script de Preparación

Este script instalará Docker, Docker Compose, configurará el firewall y preparará el sistema.

```bash
chmod +x scripts/prepare-ubuntu-server.sh
sudo ./scripts/prepare-ubuntu-server.sh
```

El script realizará las siguientes acciones:
- Actualizar el sistema operativo
- Instalar Docker Engine y Docker Compose
- Configurar UFW (firewall) con reglas de seguridad
- Crear usuario de despliegue (opcional)
- Configurar límites del sistema

**Nota**: Después de ejecutar este script, es necesario cerrar sesión y volver a conectarse para que los cambios de grupo Docker surtan efecto.

```bash
exit
ssh usuario@ip-del-servidor
cd patrimonio-drtc
```

## Configuración de Variables de Entorno

### Paso 4: Configurar Variables de Entorno

Ejecute el script de configuración para generar el archivo `.env.prod`:

```bash
chmod +x scripts/configure-env.sh
./scripts/configure-env.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

El script le solicitará:
- **Dominio**: El dominio donde se desplegará el sistema
- **Email**: Email para notificaciones y certificados SSL
- **Claves de reCAPTCHA**: Public key y private key de Google reCAPTCHA
- **Configuración de Email**: Servidor SMTP, usuario y contraseña
- **Código de eliminación permanente**: Código de seguridad para eliminaciones

El script generará automáticamente:
- `SECRET_KEY`: Clave secreta de Django (50+ caracteres)
- `POSTGRES_PASSWORD`: Contraseña segura para PostgreSQL
- `REDIS_PASSWORD`: Contraseña segura para Redis

### Paso 5: Revisar y Ajustar Variables (Opcional)

Puede editar manualmente el archivo `.env.prod` si necesita ajustar alguna configuración:

```bash
nano .env.prod
```

Variables importantes a revisar:
- `ALLOWED_HOSTS`: Debe incluir su dominio
- `DJANGO_SUPERUSER_USERNAME`: Usuario administrador inicial
- `DJANGO_SUPERUSER_PASSWORD`: Contraseña del administrador
- `DJANGO_SUPERUSER_EMAIL`: Email del administrador

## Despliegue del Sistema

### Paso 6: Ejecutar Script de Despliegue

Ejecute el script principal de despliegue:

```bash
chmod +x scripts/deploy-ubuntu.sh
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

#### Opciones Disponibles

```bash
./scripts/deploy-ubuntu.sh [OPCIONES]

Opciones:
  --domain DOMAIN       Dominio del servidor (requerido)
  --email EMAIL         Email para notificaciones y SSL (requerido)
  --branch BRANCH       Rama de Git a desplegar (default: main)
  --skip-ssl            Omitir configuración de SSL
  --skip-backup-config  Omitir configuración de backups automáticos
  --repo-url URL        URL del repositorio Git (opcional)
  --help                Mostrar ayuda
```

#### Ejemplos de Uso

**Despliegue completo con SSL:**
```bash
./scripts/deploy-ubuntu.sh --domain patrimonio.drtcpuno.gob.pe --email admin@drtcpuno.gob.pe
```

**Despliegue sin SSL (para pruebas):**
```bash
./scripts/deploy-ubuntu.sh --domain patrimonio.drtcpuno.gob.pe --email admin@drtcpuno.gob.pe --skip-ssl
```

**Despliegue desde una rama específica:**
```bash
./scripts/deploy-ubuntu.sh --domain patrimonio.drtcpuno.gob.pe --email admin@drtcpuno.gob.pe --branch develop
```

### Paso 7: Proceso de Despliegue

El script ejecutará automáticamente los siguientes pasos:

1. ✅ Validación de pre-requisitos
2. ✅ Actualización del código fuente
3. ✅ Carga de variables de entorno
4. ✅ Construcción de imágenes Docker
5. ✅ Inicio de servicios de base de datos
6. ✅ Espera de disponibilidad de PostgreSQL
7. ✅ Ejecución de migraciones
8. ✅ Creación de superusuario
9. ✅ Configuración de papelera de reciclaje
10. ✅ Recolección de archivos estáticos
11. ✅ Configuración de SSL/TLS (Let's Encrypt)
12. ✅ Inicio de todos los servicios
13. ✅ Health checks post-despliegue
14. ✅ Configuración de backups automáticos

**Tiempo estimado**: 10-15 minutos

## Verificación Post-Despliegue

### Paso 8: Verificar Servicios

Después del despliegue, verifique que todos los servicios estén funcionando:

```bash
cd patrimonio-drtc
docker-compose -f docker-compose.prod.yml ps
```

Debería ver todos los servicios en estado "Up":
- `db` (PostgreSQL)
- `redis`
- `web` (Django + Gunicorn)
- `celery-worker`
- `celery-beat`
- `nginx`

### Paso 9: Verificar Acceso Web

Acceda a las siguientes URLs desde su navegador:

- **Página principal**: `https://tu-dominio.com`
- **Panel de administración**: `https://tu-dominio.com/admin/`
- **Health check**: `https://tu-dominio.com/health/`
- **Health check detallado**: `https://tu-dominio.com/health/detailed/`

### Paso 10: Verificar SSL

Verifique que el certificado SSL esté correctamente instalado:

```bash
echo | openssl s_client -connect tu-dominio.com:443 -servername tu-dominio.com 2>/dev/null | openssl x509 -noout -dates
```

### Paso 11: Verificar Logs

Revise los logs para asegurarse de que no hay errores:

```bash
# Ver logs de todos los servicios
docker-compose -f docker-compose.prod.yml logs --tail=100

# Ver logs de un servicio específico
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs celery-worker
docker-compose -f docker-compose.prod.yml logs nginx
```

## Comandos Útiles

### Gestión de Servicios

```bash
# Ver estado de servicios
docker-compose -f docker-compose.prod.yml ps

# Ver logs en tiempo real
docker-compose -f docker-compose.prod.yml logs -f

# Ver logs de un servicio específico
docker-compose -f docker-compose.prod.yml logs -f web

# Reiniciar todos los servicios
docker-compose -f docker-compose.prod.yml restart

# Reiniciar un servicio específico
docker-compose -f docker-compose.prod.yml restart web

# Detener todos los servicios
docker-compose -f docker-compose.prod.yml down

# Iniciar todos los servicios
docker-compose -f docker-compose.prod.yml up -d
```

### Gestión de Base de Datos

```bash
# Acceder a PostgreSQL
docker-compose -f docker-compose.prod.yml exec db psql -U patrimonio -d patrimonio

# Crear backup manual
docker-compose -f docker-compose.prod.yml exec db pg_dump -U patrimonio patrimonio > backup_$(date +%Y%m%d).sql

# Restaurar backup
cat backup_20241112.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U patrimonio patrimonio
```

### Gestión de Django

```bash
# Acceder a shell de Django
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# Crear superusuario adicional
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Ejecutar comando de gestión
docker-compose -f docker-compose.prod.yml exec web python manage.py [comando]

# Ver migraciones aplicadas
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations
```

### Gestión de Celery

```bash
# Ver workers activos
docker-compose -f docker-compose.prod.yml exec celery-worker celery -A patrimonio inspect active

# Ver tareas programadas
docker-compose -f docker-compose.prod.yml exec celery-worker celery -A patrimonio inspect scheduled

# Ver estadísticas
docker-compose -f docker-compose.prod.yml exec celery-worker celery -A patrimonio inspect stats
```

### Monitoreo

```bash
# Ver uso de recursos
docker stats

# Ver espacio en disco
df -h

# Ver logs del sistema
tail -f /var/log/patrimonio-deploy.log

# Ver logs de backups
tail -f /var/log/patrimonio-backup.log
```

## Troubleshooting

### Problema: Docker no está instalado

**Síntoma**: Error "Docker no está instalado"

**Solución**:
```bash
sudo ./scripts/prepare-ubuntu-server.sh
```

### Problema: Permisos de Docker

**Síntoma**: Error "permission denied while trying to connect to the Docker daemon"

**Solución**:
```bash
sudo usermod -aG docker $USER
# Cerrar sesión y volver a conectarse
exit
ssh usuario@ip-del-servidor
```

### Problema: PostgreSQL no responde

**Síntoma**: Error "PostgreSQL no respondió después de X intentos"

**Solución**:
```bash
# Ver logs de PostgreSQL
docker-compose -f docker-compose.prod.yml logs db

# Reiniciar PostgreSQL
docker-compose -f docker-compose.prod.yml restart db

# Verificar estado
docker-compose -f docker-compose.prod.yml exec db pg_isready -U patrimonio
```

### Problema: Migraciones fallan

**Síntoma**: Error al aplicar migraciones

**Solución**:
```bash
# Ver logs detallados
docker-compose -f docker-compose.prod.yml logs web

# Intentar migraciones manualmente
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --verbosity 3

# Si persiste, verificar base de datos
docker-compose -f docker-compose.prod.yml exec db psql -U patrimonio -d patrimonio -c "\dt"
```

### Problema: SSL no se configura

**Síntoma**: Error al obtener certificado de Let's Encrypt

**Solución**:
```bash
# Verificar que el dominio apunta al servidor
nslookup tu-dominio.com

# Verificar que el puerto 80 está abierto
sudo ufw status

# Intentar configuración SSL manualmente
./scripts/setup-ssl.sh tu-dominio.com tu-email@ejemplo.com
```

### Problema: Servicios no inician

**Síntoma**: Contenedores en estado "Restarting" o "Exited"

**Solución**:
```bash
# Ver logs del servicio problemático
docker-compose -f docker-compose.prod.yml logs [servicio]

# Verificar configuración
docker-compose -f docker-compose.prod.yml config

# Reconstruir imágenes
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Problema: Espacio en disco insuficiente

**Síntoma**: Error "no space left on device"

**Solución**:
```bash
# Ver uso de disco
df -h

# Limpiar imágenes Docker no utilizadas
docker system prune -a

# Limpiar volúmenes no utilizados
docker volume prune

# Limpiar logs antiguos
sudo find /var/log -name "*.log" -mtime +30 -delete
```

## Actualización del Sistema

Para actualizar el sistema a una nueva versión:

```bash
cd patrimonio-drtc

# Opción 1: Actualización completa (recomendado)
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com

# Opción 2: Actualización manual
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml restart
```

## Rollback

Si necesita revertir a una versión anterior:

```bash
# Ver commits recientes
git log --oneline -10

# Revertir a un commit específico
git checkout [commit-hash]

# Reconstruir y reiniciar
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Restaurar base de datos si es necesario
cat backups/db/patrimonio_[fecha].sql.gz | gunzip | docker-compose -f docker-compose.prod.yml exec -T db psql -U patrimonio patrimonio
```

## Mantenimiento Regular

### Backups

Los backups se ejecutan automáticamente todos los días a las 3:00 AM. Los archivos se guardan en:
- Base de datos: `backups/db/`
- Archivos media: `backups/media/`

Para crear un backup manual:
```bash
./scripts/backup.sh
```

### Monitoreo

Revise regularmente:
- Logs del sistema
- Uso de recursos (CPU, RAM, disco)
- Estado de servicios
- Certificados SSL (renovación automática cada 60 días)

### Actualizaciones de Seguridad

Mantenga el sistema actualizado:
```bash
# Actualizar sistema operativo
sudo apt update && sudo apt upgrade -y

# Actualizar Docker
sudo apt install docker-ce docker-ce-cli containerd.io

# Actualizar aplicación
cd patrimonio-drtc
git pull origin main
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

## Soporte

Para soporte adicional:
- Revise la documentación en `docs/`
- Consulte los logs en `/var/log/patrimonio-*.log`
- Contacte al equipo de desarrollo

---

**Última actualización**: Noviembre 2024
