# 🔧 Fix: Redis Unhealthy

## Problema
Redis no está arrancando correctamente y marca como "unhealthy"

## Diagnóstico

### Ver logs de Redis:
```bash
docker compose -f docker-compose.simple.yml logs redis
```

### Ver logs de DB:
```bash
docker compose -f docker-compose.simple.yml logs db
```

## Soluciones Posibles

### Solución 1: Verificar .env.prod

Asegúrate de que tu archivo `.env.prod` tenga todas las variables:

```bash
# Ver si existe
ls -la .env.prod

# Ver contenido (sin mostrar contraseñas)
cat .env.prod | grep -v PASSWORD
```

### Solución 2: Reiniciar solo Redis y DB

```bash
# Detener todo
docker compose -f docker-compose.simple.yml down

# Eliminar volúmenes (CUIDADO: borra datos)
docker volume rm sistema_patrimonio_drtc_redis_data
docker volume rm sistema_patrimonio_drtc_postgres_data

# Iniciar solo DB y Redis
docker compose -f docker-compose.simple.yml up -d db redis

# Ver logs en tiempo real
docker compose -f docker-compose.simple.yml logs -f db redis
```

### Solución 3: Verificar que REDIS_PASSWORD esté configurado

El healthcheck de Redis necesita la contraseña. Verifica que esté en `.env.prod`:

```bash
grep REDIS_PASSWORD .env.prod
```

Debe tener algo como:
```
REDIS_PASSWORD=tu_password_seguro_aqui
```

### Solución 4: Probar Redis manualmente

```bash
# Entrar al contenedor de Redis
docker compose -f docker-compose.simple.yml exec redis sh

# Dentro del contenedor, probar conexión
redis-cli -a TU_PASSWORD ping
# Debería responder: PONG

# Salir
exit
```

## Comandos de Diagnóstico Completo

```bash
# Ver estado de todos los contenedores
docker compose -f docker-compose.simple.yml ps

# Ver logs de todos los servicios
docker compose -f docker-compose.simple.yml logs

# Ver solo errores
docker compose -f docker-compose.simple.yml logs | grep -i error

# Reiniciar un servicio específico
docker compose -f docker-compose.simple.yml restart redis
```

## Si Nada Funciona: Despliegue Limpio

```bash
# 1. Detener y limpiar TODO
docker compose -f docker-compose.simple.yml down -v
docker system prune -af

# 2. Verificar .env.prod existe y tiene todas las variables
cat .env.prod

# 3. Iniciar paso a paso
docker compose -f docker-compose.simple.yml up -d db
# Esperar 30 segundos
docker compose -f docker-compose.simple.yml up -d redis
# Esperar 20 segundos
docker compose -f docker-compose.simple.yml up -d web
# Esperar 30 segundos
docker compose -f docker-compose.simple.yml up -d celery celery-beat nginx
```

## Verificación Final

```bash
# Todos los contenedores deben estar "healthy" o "running"
docker compose -f docker-compose.simple.yml ps

# Debería mostrar algo como:
# NAME                                    STATUS
# sistema_patrimonio_drtc-db-1           Up (healthy)
# sistema_patrimonio_drtc-redis-1        Up (healthy)
# sistema_patrimonio_drtc-web-1          Up (healthy)
# sistema_patrimonio_drtc-celery-1       Up
# sistema_patrimonio_drtc-celery-beat-1  Up
# sistema_patrimonio_drtc-nginx-1        Up (healthy)
```
