# 🚀 Guía Rápida de Despliegue - Sistema de Patrimonio DRTC

## 📋 Requisitos Previos

Necesitas:
- Un servidor Ubuntu (20.04 o superior)
- Acceso SSH al servidor
- Un dominio apuntando a la IP del servidor
- Email para notificaciones

## 🎯 Pasos para Desplegar

### 1️⃣ Conectarse al Servidor

```bash
ssh usuario@tu-servidor.com
```

### 2️⃣ Clonar el Repositorio

```bash
git clone https://github.com/ajahuanex/sistema_patrimonio_drtc.git
cd sistema_patrimonio_drtc
```

### 3️⃣ Preparar el Servidor (Solo la primera vez)

Este paso instala Docker, configura el firewall y prepara todo:

```bash
chmod +x scripts/prepare-ubuntu-server.sh
sudo ./scripts/prepare-ubuntu-server.sh
```

**⚠️ IMPORTANTE**: Después de este paso, cierra sesión y vuelve a conectarte:

```bash
exit
ssh usuario@tu-servidor.com
cd sistema_patrimonio_drtc
```

### 4️⃣ Configurar Variables de Entorno

```bash
chmod +x scripts/configure-env.sh
./scripts/configure-env.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

El script te pedirá:
- **Claves de reCAPTCHA**: Obtener en https://www.google.com/recaptcha/admin
- **Configuración de Email**: Servidor SMTP, usuario y contraseña
- **Código de seguridad**: Para eliminaciones permanentes

### 5️⃣ Desplegar el Sistema

```bash
chmod +x scripts/deploy-ubuntu.sh
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

⏱️ **Tiempo estimado**: 10-15 minutos

El script hará automáticamente:
- ✅ Construir las imágenes Docker
- ✅ Iniciar la base de datos
- ✅ Aplicar migraciones
- ✅ Crear el usuario administrador
- ✅ Configurar SSL (certificado HTTPS)
- ✅ Iniciar todos los servicios
- ✅ Configurar backups automáticos

### 6️⃣ Verificar que Todo Funciona

```bash
# Ver estado de los servicios
docker-compose -f docker-compose.prod.yml ps
```

Todos los servicios deben estar en estado "Up":
- ✅ db (PostgreSQL)
- ✅ redis
- ✅ web (Django)
- ✅ celery-worker
- ✅ celery-beat
- ✅ nginx

### 7️⃣ Acceder al Sistema

Abre tu navegador y ve a:
- **Página principal**: `https://tu-dominio.com`
- **Panel de administración**: `https://tu-dominio.com/admin/`

## 🔧 Comandos Útiles

### Ver Logs en Tiempo Real
```bash
# Todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Solo el servidor web
docker-compose -f docker-compose.prod.yml logs -f web
```

### Reiniciar Servicios
```bash
# Todos los servicios
docker-compose -f docker-compose.prod.yml restart

# Solo un servicio
docker-compose -f docker-compose.prod.yml restart web
```

### Crear Backup Manual
```bash
./scripts/backup.sh
```

### Actualizar el Sistema
```bash
cd sistema_patrimonio_drtc
git pull origin main
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

## 🆘 Solución de Problemas

### ❌ Error: "Docker no está instalado"
```bash
sudo ./scripts/prepare-ubuntu-server.sh
```

### ❌ Error: "Permission denied" con Docker
```bash
sudo usermod -aG docker $USER
exit
# Vuelve a conectarte
ssh usuario@tu-servidor.com
```

### ❌ PostgreSQL no responde
```bash
docker-compose -f docker-compose.prod.yml restart db
docker-compose -f docker-compose.prod.yml logs db
```

### ❌ SSL no se configura
```bash
# Verifica que tu dominio apunte al servidor
nslookup tu-dominio.com

# Verifica el firewall
sudo ufw status

# Los puertos 80 y 443 deben estar abiertos
```

## 📊 Monitoreo

### Ver Estado de Salud del Sistema
```bash
# Desde el navegador
https://tu-dominio.com/health/

# Desde la terminal
curl https://tu-dominio.com/health/
```

### Ver Uso de Recursos
```bash
docker stats
```

### Ver Espacio en Disco
```bash
df -h
```

## 🔄 Backups Automáticos

Los backups se ejecutan automáticamente todos los días a las 3:00 AM.

Los archivos se guardan en:
- Base de datos: `backups/db/`
- Archivos media: `backups/media/`

## 📚 Documentación Completa

Para más detalles, consulta:
- `docs/DEPLOYMENT_UBUNTU.md` - Guía completa de despliegue
- `scripts/DEPLOY_QUICK_START.md` - Guía rápida en inglés
- `docs/BACKUP_SYSTEM.md` - Sistema de respaldos
- `docs/HEALTH_CHECKS.md` - Monitoreo de salud

## 🎉 ¡Listo!

Tu sistema de patrimonio está desplegado y funcionando.

**Credenciales de administrador**:
- Usuario: (el que configuraste en `.env.prod`)
- Contraseña: (la que configuraste en `.env.prod`)

**URLs importantes**:
- Sistema: `https://tu-dominio.com`
- Admin: `https://tu-dominio.com/admin/`
- Health: `https://tu-dominio.com/health/`

---

**¿Necesitas ayuda?** Revisa los logs:
```bash
docker-compose -f docker-compose.prod.yml logs
```
