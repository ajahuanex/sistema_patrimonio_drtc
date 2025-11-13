# Despliegue Completo desde Git - IP 161.132.47.92

## Proceso Completo: De Git a Producción

Este documento muestra el proceso completo desde clonar el repositorio hasta tener la aplicación corriendo.

---

## OPCIÓN 1: Despliegue Automatizado (Un Solo Comando)

### 1. Clonar el repositorio
```bash
cd /opt
git clone https://github.com/ajahuanex/sistema_patrimonio_drtc.git
cd sistema_patrimonio_drtc
```

### 2. Ejecutar script de despliegue
```bash
chmod +x scripts/deploy-ip-161.sh
./scripts/deploy-ip-161.sh
```

**¡Eso es todo!** El script hace todo automáticamente y verás el progreso en pantalla.

---

## OPCIÓN 2: Despliegue Manual (Paso a Paso)

### PASO 1: Clonar el Repositorio

```bash
# Ir al directorio donde quieres instalar
cd /opt

# Clonar desde GitHub
git clone https://github.com/ajahuanex/sistema_patrimonio_drtc.git

# Entrar al directorio
cd sistema_patrimonio_drtc

# Ver el contenido
ls -la
```

**Verás algo como:**
```
drwxr-xr-x  apps/
drwxr-xr-x  docs/
drwxr-xr-x  nginx/
drwxr-xr-x  patrimonio/
drwxr-xr-x  scripts/
-rw-r--r--  .env.prod.ip-only
-rw-r--r--  docker-compose.prod.yml
-rw-r--r--  Dockerfile.prod
-rw-r--r--  manage.py
-rw-r--r--  requirements.txt
```

---

### PASO 2: Crear Archivo de Configuración .env.prod

#### Opción A: Generar automáticamente con script

```bash
# Dar permisos al script
chmod +x scripts/generar-env-prod.sh

# Ejecutar el script
./scripts/generar-env-prod.sh
```

El script te preguntará:
```
Email para notificaciones (ej: tu-email@gmail.com): miempresa@gmail.com
Contraseña de aplicación de Gmail (16 caracteres): ****************
Email para reCAPTCHA (opcional, Enter para omitir): [Enter]
```

Y generará automáticamente:
- SECRET_KEY seguro
- Contraseñas para PostgreSQL y Redis
- Código de eliminación permanente
- Archivo .env.prod completo

**IMPORTANTE:** Guarda las credenciales que muestra el script.

#### Opción B: Crear manualmente

```bash
# Copiar la plantilla
cp .env.prod.ip-only .env.prod

# Editar el archivo
nano .env.prod
```

Cambia estos valores:
```bash
SECRET_KEY=tu-clave-generada-aqui
POSTGRES_PASSWORD=tu-password-postgres
REDIS_PASSWORD=tu-password-redis
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password-gmail
PERMANENT_DELETE_CODE=tu-codigo-seguro
```

Para generar SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Guarda con `Ctrl+O`, Enter, `Ctrl+X`

---

### PASO 3: Configurar Nginx para HTTP

```bash
# Copiar configuración HTTP-only
cp nginx/nginx.http-only.conf nginx/nginx.prod.conf

# Verificar que se copió
ls -l nginx/nginx.prod.conf
```

---

### PASO 4: Crear Directorios Necesarios

```bash
# Crear directorios
mkdir -p logs backups nginx/logs

# Dar permisos
chmod -R 755 logs backups nginx/logs

# Verificar
ls -ld logs backups nginx/logs
```

---

### PASO 5: Construir las Imágenes Docker

```bash
# Construir todas las imágenes
docker compose -f docker-compose.prod.yml build

# Verás algo como:
# [+] Building 234.5s (23/23) FINISHED
# => [web internal] load build definition
# => [web] transferring dockerfile
# => [web] FROM docker.io/library/python:3.11-slim
# ...
```

Este proceso tarda 5-10 minutos. Verás el progreso en pantalla.

---

### PASO 6: Iniciar los Servicios

```bash
# Iniciar todos los servicios en segundo plano
docker compose -f docker-compose.prod.yml up -d

# Verás:
# [+] Running 8/8
#  ✔ Network patrimonio_network       Created
#  ✔ Volume "postgres_data"           Created
#  ✔ Volume "redis_data"              Created
#  ✔ Volume "media_files"             Created
#  ✔ Volume "static_files"            Created
#  ✔ Container patrimonio-db-1        Started
#  ✔ Container patrimonio-redis-1     Started
#  ✔ Container patrimonio-web-1       Started
#  ✔ Container patrimonio-celery-1    Started
#  ✔ Container patrimonio-celery-beat-1 Started
#  ✔ Container patrimonio-nginx-1     Started
```

---

### PASO 7: Verificar Estado de los Servicios

```bash
# Ver estado
docker compose -f docker-compose.prod.yml ps
```

**Espera 1-2 minutos** hasta que veas algo como:
```
NAME                          STATUS              PORTS
patrimonio-db-1               Up (healthy)        5432/tcp
patrimonio-redis-1            Up (healthy)        6379/tcp
patrimonio-web-1              Up (healthy)        8000/tcp
patrimonio-celery-1           Up (healthy)        
patrimonio-celery-beat-1      Up (healthy)        
patrimonio-nginx-1            Up (healthy)        0.0.0.0:80->80/tcp
```

Si algún servicio está "unhealthy", espera un poco más o revisa los logs:
```bash
docker compose -f docker-compose.prod.yml logs web
```

---

### PASO 8: Ejecutar Migraciones de Base de Datos

```bash
# Ejecutar migraciones
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Verás:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, sessions, bienes, ...
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ...
```

---

### PASO 9: Crear Superusuario

```bash
# Crear superusuario
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Te preguntará:
```
Username (leave blank to use 'app'): admin
Email address: admin@patrimonio.com
Password: ********
Password (again): ********
Superuser created successfully.
```

---

### PASO 10: Recolectar Archivos Estáticos

```bash
# Recolectar estáticos
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Verás:
# 142 static files copied to '/app/static'.
```

---

### PASO 11: Verificar Health Checks

```bash
# Health check básico
curl http://localhost/health/
```

**Respuesta esperada:**
```json
{
    "status": "healthy",
    "timestamp": "2024-11-13T10:30:00.000000Z",
    "version": "1.0.0"
}
```

```bash
# Health check detallado
curl http://localhost/health/detailed/
```

**Respuesta esperada:**
```json
{
    "status": "healthy",
    "timestamp": "2024-11-13T10:30:00.000000Z",
    "version": "1.0.0",
    "services": {
        "database": {
            "status": "healthy",
            "response_time_ms": 5,
            "message": "Database connection successful"
        },
        "redis": {
            "status": "healthy",
            "response_time_ms": 2,
            "message": "Redis connection successful"
        },
        "celery": {
            "status": "healthy",
            "response_time_ms": 150,
            "active_workers": 4,
            "active_tasks": 0,
            "message": "4 worker(s) active"
        }
    }
}
```

---

### PASO 12: Acceder a la Aplicación

Abre tu navegador y accede a:

**Desde el servidor:**
- http://localhost
- http://localhost/admin/
- http://localhost/health/detailed/

**Desde cualquier computadora:**
- http://161.132.47.92
- http://161.132.47.92/admin/
- http://161.132.47.92/health/detailed/

---

## Ver Logs en Tiempo Real

```bash
# Ver logs de todos los servicios
docker compose -f docker-compose.prod.yml logs -f

# Ver logs de un servicio específico
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f db
docker compose -f docker-compose.prod.yml logs -f redis
docker compose -f docker-compose.prod.yml logs -f celery
docker compose -f docker-compose.prod.yml logs -f nginx

# Presiona Ctrl+C para salir
```

---

## Comandos Útiles Post-Despliegue

### Ver estado de servicios
```bash
docker compose -f docker-compose.prod.yml ps
```

### Reiniciar un servicio
```bash
docker compose -f docker-compose.prod.yml restart web
```

### Reiniciar todos los servicios
```bash
docker compose -f docker-compose.prod.yml restart
```

### Detener todos los servicios
```bash
docker compose -f docker-compose.prod.yml down
```

### Iniciar servicios detenidos
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Ver uso de recursos
```bash
docker stats
```

### Entrar a un contenedor
```bash
# Entrar al contenedor web
docker compose -f docker-compose.prod.yml exec web bash

# Entrar a PostgreSQL
docker compose -f docker-compose.prod.yml exec db psql -U patrimonio_user patrimonio_prod

# Entrar a Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli -a $REDIS_PASSWORD
```

---

## Actualizar la Aplicación desde Git

Cuando haya cambios en GitHub:

```bash
# 1. Ir al directorio
cd /opt/sistema_patrimonio_drtc

# 2. Detener servicios
docker compose -f docker-compose.prod.yml down

# 3. Actualizar código
git pull origin main

# 4. Reconstruir imágenes
docker compose -f docker-compose.prod.yml build

# 5. Iniciar servicios
docker compose -f docker-compose.prod.yml up -d

# 6. Ejecutar migraciones (si hay)
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 7. Recolectar estáticos
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 8. Verificar
docker compose -f docker-compose.prod.yml ps
curl http://localhost/health/detailed/
```

---

## Backup Manual

```bash
# Crear backup de la base de datos
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U patrimonio_user patrimonio_prod > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Verificar que se creó
ls -lh backups/
```

---

## Restaurar Backup

```bash
# Listar backups disponibles
ls -lh backups/

# Restaurar un backup específico
docker compose -f docker-compose.prod.yml exec -T db psql -U patrimonio_user patrimonio_prod < backups/backup_20241113_103000.sql
```

---

## Solución de Problemas Comunes

### Servicio "unhealthy"

```bash
# Ver logs del servicio
docker compose -f docker-compose.prod.yml logs web

# Reiniciar el servicio
docker compose -f docker-compose.prod.yml restart web

# Ver estado
docker compose -f docker-compose.prod.yml ps
```

### No puedo acceder desde el navegador

```bash
# Verificar que nginx está corriendo
docker compose -f docker-compose.prod.yml ps nginx

# Ver logs de nginx
docker compose -f docker-compose.prod.yml logs nginx

# Verificar puerto 80
sudo netstat -tlnp | grep :80

# Abrir puerto en firewall
sudo ufw allow 80/tcp
sudo ufw status
```

### Error de permisos

```bash
# Dar permisos a directorios
chmod -R 755 logs backups nginx/logs

# Verificar permisos
ls -la
```

### Limpiar todo y empezar de nuevo

```bash
# CUIDADO: Esto borra todo
docker compose -f docker-compose.prod.yml down -v
rm -rf logs/* backups/*
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

---

## Checklist de Despliegue

```
□ Repositorio clonado en /opt/sistema_patrimonio_drtc
□ Archivo .env.prod creado con credenciales seguras
□ Configuración nginx.prod.conf copiada
□ Directorios logs, backups creados
□ Imágenes Docker construidas
□ Servicios iniciados (docker compose up -d)
□ Todos los servicios en estado "healthy"
□ Migraciones ejecutadas
□ Superusuario creado
□ Archivos estáticos recolectados
□ Health checks funcionando
□ Acceso web verificado (http://161.132.47.92)
□ Panel admin accesible (http://161.132.47.92/admin/)
```

---

## Resumen de Comandos Rápidos

```bash
# Clonar y entrar
cd /opt
git clone https://github.com/ajahuanex/sistema_patrimonio_drtc.git
cd sistema_patrimonio_drtc

# Configurar
./scripts/generar-env-prod.sh
cp nginx/nginx.http-only.conf nginx/nginx.prod.conf
mkdir -p logs backups nginx/logs

# Desplegar
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Verificar
docker compose -f docker-compose.prod.yml ps
curl http://localhost/health/detailed/
```

---

**¡Listo! Tu aplicación está corriendo en http://161.132.47.92** 🎉
