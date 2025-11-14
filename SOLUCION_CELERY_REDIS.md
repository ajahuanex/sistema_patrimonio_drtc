# ✅ Solución: Celery Conectándose a Redis

## 🔍 Problema Identificado

Celery estaba intentando conectarse a RabbitMQ (`amqp://guest:**@127.0.0.1:5672//`) en lugar de Redis, causando errores continuos y reinic ios de los contenedores.

## 🛠️ Cambios Realizados

### 1. Archivo `.env` en el Servidor
Se agregaron/corrigieron las siguientes variables:
```bash
DJANGO_SETTINGS_MODULE=patrimonio.settings
REDIS_URL=redis://redis:6379/0
```

### 2. Archivo `docker-compose.yml` (Local)
Se agregaron las variables de entorno faltantes a los servicios `celery` y `celery-beat`:
```yaml
environment:
  - CELERY_BROKER_URL=redis://redis:6379/0
  - DJANGO_SETTINGS_MODULE=patrimonio.settings
```

## 📋 Próximos Pasos

### Paso 1: Subir cambios a GitHub
```bash
git add docker-compose.yml
git commit -m "fix: Agregar variables de entorno para Celery Redis"
git push origin main
```

### Paso 2: Actualizar en el Servidor
Conéctate por SSH y ejecuta:
```bash
ssh administrador@161.132.47.92
cd ~/dockers/sistema_patrimonio_drtc

# Traer cambios de GitHub
git pull origin main

# Reconstruir y reiniciar contenedores
docker compose down celery celery-beat
docker compose build celery celery-beat
docker compose up -d celery celery-beat

# Verificar estado
docker compose ps
docker compose logs celery --tail=20
```

### Paso 3: Verificar que Celery esté funcionando
```bash
# Ver logs de celery
docker compose logs celery --tail=30

# Deberías ver algo como:
# [2025-11-14 XX:XX:XX,XXX: INFO/MainProcess] Connected to redis://redis:6379/0
# [2025-11-14 XX:XX:XX,XXX: INFO/MainProcess] celery@hostname ready.
```

## ✅ Resultado Esperado

Después de aplicar estos cambios:
- ✅ Celery se conectará correctamente a Redis
- ✅ Los contenedores `celery` y `celery-beat` estarán en estado "Up" y "healthy"
- ✅ Las tareas programadas funcionarán correctamente
- ✅ No habrá más errores de conexión a RabbitMQ

## 📝 Notas

- El archivo `docker-compose.yml` local ya fue actualizado
- Necesitas hacer commit y push de los cambios
- Luego actualizar en el servidor con `git pull`
- Finalmente reconstruir los contenedores de Celery
