# Guía Rápida de Despliegue

Esta guía proporciona los pasos esenciales para desplegar el sistema en un servidor Ubuntu.

## Pasos Rápidos

### 1. Preparar el Servidor (Una sola vez)

```bash
# Conectarse al servidor
ssh usuario@ip-del-servidor

# Clonar repositorio
git clone https://github.com/tu-org/patrimonio-drtc.git
cd patrimonio-drtc

# Preparar servidor (instala Docker, configura firewall, etc.)
chmod +x scripts/prepare-ubuntu-server.sh
sudo ./scripts/prepare-ubuntu-server.sh

# Cerrar sesión y reconectar (para aplicar cambios de grupo Docker)
exit
ssh usuario@ip-del-servidor
cd patrimonio-drtc
```

### 2. Configurar Variables de Entorno

```bash
# Configurar variables de entorno
chmod +x scripts/configure-env.sh
./scripts/configure-env.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

El script te pedirá:
- Claves de reCAPTCHA (obtener en https://www.google.com/recaptcha/admin)
- Configuración de email SMTP
- Código de eliminación permanente

### 3. Desplegar el Sistema

```bash
# Despliegue completo con SSL
chmod +x scripts/deploy-ubuntu.sh
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

**Tiempo estimado**: 10-15 minutos

### 4. Verificar Despliegue

```bash
# Ver estado de servicios
docker-compose -f docker-compose.prod.yml ps

# Acceder al sistema
# https://tu-dominio.com
# https://tu-dominio.com/admin/
```

## Comandos Útiles

### Ver Logs
```bash
# Todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Servicio específico
docker-compose -f docker-compose.prod.yml logs -f web
```

### Reiniciar Servicios
```bash
# Todos los servicios
docker-compose -f docker-compose.prod.yml restart

# Servicio específico
docker-compose -f docker-compose.prod.yml restart web
```

### Crear Backup Manual
```bash
./scripts/backup.sh
```

### Actualizar Sistema
```bash
# Actualizar a última versión
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

## Solución de Problemas Comunes

### Error: Docker no instalado
```bash
sudo ./scripts/prepare-ubuntu-server.sh
```

### Error: Permisos de Docker
```bash
sudo usermod -aG docker $USER
exit
# Reconectar
```

### Error: PostgreSQL no responde
```bash
docker-compose -f docker-compose.prod.yml restart db
docker-compose -f docker-compose.prod.yml logs db
```

### Error: SSL no se configura
```bash
# Verificar DNS
nslookup tu-dominio.com

# Verificar firewall
sudo ufw status

# Intentar SSL manualmente
./scripts/setup-ssl.sh tu-dominio.com tu-email@ejemplo.com
```

## Documentación Completa

Para información detallada, consulte:
- `docs/DEPLOYMENT_UBUNTU.md` - Guía completa de despliegue
- `scripts/deploy-ubuntu.sh --help` - Ayuda del script

## Soporte

- Logs del sistema: `/var/log/patrimonio-deploy.log`
- Logs de Docker: `docker-compose -f docker-compose.prod.yml logs`
- Documentación: `docs/`
