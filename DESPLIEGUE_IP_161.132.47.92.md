# Guía Completa de Despliegue para IP 161.132.47.92

## Requisitos Previos
- Servidor Ubuntu con Docker y Docker Compose instalados
- Acceso directo al servidor (consola o VNC, no SSH)
- IP: 161.132.47.92

---

## OPCIÓN 1: Despliegue Automatizado (Recomendado)

### PASO 1: Clonar el Repositorio

```bash
# Ir al directorio /opt
cd /opt

# Clonar el repositorio
git clone https://github.com/ajahuanex/sistema_patrimonio_drtc.git

# Entrar al directorio
cd sistema_patrimonio_drtc
```

### PASO 2: Ejecutar Script de Despliegue Automatizado

```bash
# Dar permisos de ejecución
chmod +x scripts/deploy-ip-161.sh

# Ejecutar el script
./scripts/deploy-ip-161.sh
```

El script hará TODO automáticamente:
- ✓ Verificar requisitos (Docker, Docker Compose, Git)
- ✓ Generar archivo .env.prod con credenciales seguras
- ✓ Configurar Nginx para HTTP
- ✓ Crear directorios necesarios
- ✓ Construir imágenes Docker
- ✓ Iniciar servicios
- ✓ Ejecutar migraciones
- ✓ Crear superusuario (te pedirá los datos)
- ✓ Recolectar archivos estáticos
- ✓ Verificar health checks

**Verás todo el proceso en pantalla con colores y mensajes claros.**

---

## OPCIÓN 2: Despliegue Manual Paso a Paso

### PASO 1: Clonar el Repositorio

```bash
cd /opt
git clone https://github.com/ajahuanex/sistema_patrimonio_drtc.git
cd sistema_patrimonio_drtc
```

### PASO 2: Generar Archivo .env.prod

### Opción A: Usar el Script Generador (Recomendado)

```bash
# Dar permisos de ejecución al script
chmod +x scripts/generar-env-prod.sh

# Ejecutar el script
./scripts/generar-env-prod.sh
```

El script te pedirá:
1. **Email para notificaciones**: Tu email de Gmail
2. **Contraseña de aplicación de Gmail**: Genera una en https://myaccount.google.com/apppasswords
3. **Email para reCAPTCHA** (opcional): Presiona Enter para omitir

El script generará automáticamente:
- SECRET_KEY de Django
- Contraseña de PostgreSQL
- Contraseña de Redis
- Código de eliminación permanente

**IMPORTANTE**: Guarda las credenciales que muestra el script en un lugar seguro.

### Opción B: Copiar el Archivo Plantilla Manualmente

```bash
# Copiar el archivo plantilla
cp .env.prod.ip-only .env.prod

# Editar el archivo
nano .env.prod
```

Debes cambiar estos valores:
- `SECRET_KEY`: Genera uno con: `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `POSTGRES_PASSWORD`: Contraseña segura para PostgreSQL
- `REDIS_PASSWORD`: Contraseña segura para Redis
- `EMAIL_HOST_USER`: Tu email de Gmail
- `EMAIL_HOST_PASSWORD`: Contraseña de aplicación de Gmail
- `PERMANENT_DELETE_CODE`: Código seguro para borrado permanente

Guarda con `Ctrl+O`, Enter, `Ctrl+X`

---

## PASO 4: Configurar Nginx para HTTP (Sin SSL)

```bash
# Copiar la configuración HTTP-only
cp nginx/nginx.http-only.conf nginx/nginx.prod.conf
```

---

## PASO 5: Ajustar docker-compose.prod.yml

```bash
# Editar docker-compose
nano docker-compose.prod.yml
```

Busca la sección `nginx:` (línea ~154) y modifícala para que quede así:

```yaml
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
      - static_files:/app/static
      - media_files:/app/media
      - ./nginx/logs:/var/log/nginx
    networks:
      - patrimonio_network
    depends_on:
      web:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Cambios importantes**:
- Eliminar puerto `443:443`
- Eliminar volúmenes de SSL y certbot
- Mantener solo puerto 80

Guarda con `Ctrl+O`, Enter, `Ctrl+X`

---

## PASO 6: Crear Directorios Necesarios

```bash
mkdir -p logs backups nginx/logs
chmod -R 755 logs backups nginx/logs
```

---

### PASO 3: Construir las Imágenes Docker

```bash
docker compose -f docker-compose.prod.yml build
```

Este proceso puede tardar 5-10 minutos.

---

### PASO 4: Iniciar los Servicios

```bash
docker compose -f docker-compose.prod.yml up -d
```

---

### PASO 5: Verificar Estado de los Servicios

```bash
# Ver estado de todos los servicios
docker compose -f docker-compose.prod.yml ps
```

Espera 1-2 minutos hasta que todos los servicios muestren estado `healthy`.

Si algún servicio está `unhealthy`, revisa los logs:
```bash
docker compose -f docker-compose.prod.yml logs [nombre-servicio]
```

---

### PASO 6: Ejecutar Migraciones de Base de Datos

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

---

### PASO 7: Crear Superusuario

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Te pedirá:
- Username (nombre de usuario)
- Email
- Password (contraseña)

---

### PASO 8: Recolectar Archivos Estáticos

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

### PASO 9: Verificar Health Checks

```bash
# Health check básico
curl http://localhost/health/

# Health check detallado
curl http://localhost/health/detailed/

# Desde fuera del servidor (en tu computadora local)
curl http://161.132.47.92/health/
```

Deberías ver respuestas JSON con `"status": "healthy"`.

---

## Acceder a la Aplicación

Abre tu navegador y accede a:

- **Aplicación principal**: http://161.132.47.92
- **Panel de administración**: http://161.132.47.92/admin/
- **Health check**: http://161.132.47.92/health/detailed/

Inicia sesión con el superusuario que creaste.

---

## Comandos Útiles Post-Despliegue

### Ver Logs
```bash
# Todos los servicios
docker compose -f docker-compose.prod.yml logs

# Servicio específico
docker compose -f docker-compose.prod.yml logs web
docker compose -f docker-compose.prod.yml logs db
docker compose -f docker-compose.prod.yml logs redis
docker compose -f docker-compose.prod.yml logs celery

# Logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f
```

### Reiniciar Servicios
```bash
# Reiniciar todos los servicios
docker compose -f docker-compose.prod.yml restart

# Reiniciar servicio específico
docker compose -f docker-compose.prod.yml restart web
```

### Detener Servicios
```bash
docker compose -f docker-compose.prod.yml down
```

### Actualizar desde GitHub
```bash
cd /opt/sistema_patrimonio_drtc
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Backup Manual de Base de Datos
```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U patrimonio_user patrimonio_prod > backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurar Backup
```bash
docker compose -f docker-compose.prod.yml exec -T db psql -U patrimonio_user patrimonio_prod < backups/backup_YYYYMMDD_HHMMSS.sql
```

---

---

## Solución de Problemas

### Servicio "unhealthy"

1. Ver logs del servicio:
```bash
docker compose -f docker-compose.prod.yml logs [servicio]
```

2. Reiniciar el servicio:
```bash
docker compose -f docker-compose.prod.yml restart [servicio]
```

### No puedo acceder desde el navegador

1. Verificar que el puerto 80 esté abierto:
```bash
sudo ufw status
sudo ufw allow 80/tcp
```

2. Verificar que nginx esté corriendo:
```bash
docker compose -f docker-compose.prod.yml ps nginx
```

### Error de conexión a base de datos

1. Verificar que PostgreSQL esté healthy:
```bash
docker compose -f docker-compose.prod.yml ps db
```

2. Verificar credenciales en .env.prod

### Error de conexión a Redis

1. Verificar que Redis esté healthy:
```bash
docker compose -f docker-compose.prod.yml ps redis
```

2. Verificar password de Redis en .env.prod

---

## Configurar Backups Automáticos (Opcional)

```bash
# Editar crontab
crontab -e

# Agregar esta línea para backup diario a las 2 AM
0 2 * * * cd /opt/sistema_patrimonio_drtc && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U patrimonio_user patrimonio_prod > backups/backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql

# Agregar esta línea para limpiar backups antiguos (más de 30 días)
0 3 * * * find /opt/sistema_patrimonio_drtc/backups -name "*.sql" -mtime +30 -delete
```

---

## Monitoreo

### Ver uso de recursos
```bash
docker stats
```

### Ver espacio en disco
```bash
df -h
```

### Ver logs del sistema
```bash
journalctl -u docker -f
```

---

## Seguridad

1. **Cambiar puerto SSH** (opcional pero recomendado):
```bash
sudo nano /etc/ssh/sshd_config
# Cambiar Port 22 a otro puerto (ej: 2222)
sudo systemctl restart sshd
```

2. **Configurar firewall**:
```bash
sudo ufw enable
sudo ufw allow 80/tcp
sudo ufw allow 22/tcp  # o tu puerto SSH personalizado
```

3. **Actualizar sistema regularmente**:
```bash
sudo apt update && sudo apt upgrade -y
```

---

## Contacto y Soporte

Si encuentras problemas durante el despliegue:

1. Revisa los logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verifica el health check: `curl http://161.132.47.92/health/detailed/`
3. Consulta la documentación en `docs/`

---

## Checklist de Despliegue

- [ ] Conectado al servidor SSH
- [ ] Repositorio clonado en /opt
- [ ] Archivo .env.prod generado con credenciales seguras
- [ ] Configuración nginx.http-only.conf copiada
- [ ] docker-compose.prod.yml ajustado (solo puerto 80)
- [ ] Directorios creados (logs, backups)
- [ ] Imágenes Docker construidas
- [ ] Servicios iniciados
- [ ] Todos los servicios en estado "healthy"
- [ ] Migraciones ejecutadas
- [ ] Superusuario creado
- [ ] Archivos estáticos recolectados
- [ ] Health checks funcionando
- [ ] Acceso web verificado (http://161.132.47.92)
- [ ] Panel admin accesible (http://161.132.47.92/admin/)
- [ ] Backups automáticos configurados (opcional)

---

**¡Despliegue completado exitosamente!** 🎉
