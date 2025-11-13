# 📋 Comandos Manuales para Despliegue

Ejecuta estos comandos uno por uno en el servidor Ubuntu.

## Paso 1: Detener todo y limpiar

```bash
# Detener contenedores existentes
docker compose -f docker-compose.simple.yml down -v

# Limpiar sistema Docker
docker system prune -f
```

## Paso 2: Cargar variables de entorno

```bash
# Cargar variables en el shell actual
set -a
source .env.prod
set +a
```

## Paso 3: Verificar que las variables están cargadas

```bash
# Verificar variables críticas
echo "POSTGRES_DB: $POSTGRES_DB"
echo "POSTGRES_USER: $POSTGRES_USER"
echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
echo "REDIS_PASSWORD: $REDIS_PASSWORD"
```

Deberías ver algo como:
```
POSTGRES_DB: patrimonio_db
POSTGRES_USER: patrimonio_user
POSTGRES_PASSWORD: patrimonio_pass_2024
REDIS_PASSWORD: redis_pass_2024
```

## Paso 4: Iniciar servicios

```bash
# Iniciar con las variables exportadas
docker compose -f docker-compose.simple.yml --env-file .env.prod up -d
```

## Paso 5: Esperar y verificar

```bash
# Esperar 60 segundos
sleep 60

# Ver estado de contenedores
docker compose -f docker-compose.simple.yml ps
```

## Paso 6: Ver logs para verificar

```bash
# Ver logs de PostgreSQL
docker compose -f docker-compose.simple.yml logs db

# Ver logs de Redis
docker compose -f docker-compose.simple.yml logs redis

# Ver logs de la aplicación web
docker compose -f docker-compose.simple.yml logs web
```

## Paso 7: Probar conexiones

```bash
# Probar PostgreSQL
docker compose -f docker-compose.simple.yml exec db pg_isready -U patrimonio_user -d patrimonio_db

# Probar Redis
docker compose -f docker-compose.simple.yml exec redis redis-cli -a redis_pass_2024 ping
```

## Si todo funciona correctamente

Deberías ver:
- PostgreSQL: `/var/run/postgresql:5432 - accepting connections`
- Redis: `PONG`

## Siguiente paso: Ejecutar migraciones

```bash
# Ejecutar migraciones de Django
docker compose -f docker-compose.simple.yml exec web python manage.py migrate

# Crear superusuario
docker compose -f docker-compose.simple.yml exec web python manage.py createsuperuser

# Recolectar archivos estáticos
docker compose -f docker-compose.simple.yml exec web python manage.py collectstatic --noinput
```

## Acceder a la aplicación

Abre en el navegador:
```
http://localhost
```

O si estás en un servidor remoto:
```
http://IP_DEL_SERVIDOR
```

## Comandos útiles adicionales

```bash
# Ver logs en tiempo real
docker compose -f docker-compose.simple.yml logs -f

# Ver logs de un servicio específico
docker compose -f docker-compose.simple.yml logs -f web
docker compose -f docker-compose.simple.yml logs -f db
docker compose -f docker-compose.simple.yml logs -f redis

# Reiniciar un servicio
docker compose -f docker-compose.simple.yml restart web

# Detener todo
docker compose -f docker-compose.simple.yml down

# Ver variables de entorno de un contenedor
docker compose -f docker-compose.simple.yml exec db env | grep POSTGRES
docker compose -f docker-compose.simple.yml exec redis env | grep REDIS
```

## Si algo falla

1. **Ver logs detallados:**
```bash
docker compose -f docker-compose.simple.yml logs --tail=100
```

2. **Verificar que .env.prod existe y tiene el formato correcto:**
```bash
cat .env.prod
```

3. **Limpiar todo y empezar de nuevo:**
```bash
docker compose -f docker-compose.simple.yml down -v
docker system prune -af
docker volume prune -f
# Luego volver al Paso 2
```

4. **Verificar que las variables se están pasando al contenedor:**
```bash
docker compose -f docker-compose.simple.yml exec db env | grep POSTGRES
```
