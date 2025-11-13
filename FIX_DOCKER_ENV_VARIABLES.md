# 🔧 Solución: Variables de Entorno en Docker

## Problema Detectado

Los contenedores de PostgreSQL y Redis no están recibiendo las variables de entorno correctamente:

- **PostgreSQL**: Error "Database is uninitialized and superuser password is not specified"
- **Redis**: Error "requirepass wrong number of arguments"

## Causa

Docker Compose no está expandiendo las variables de entorno del archivo `.env.prod` correctamente.

## Solución Rápida

### Opción 1: Usar el Script Mejorado (RECOMENDADO)

```bash
# En el servidor Ubuntu
chmod +x desplegar_servidor.sh
./desplegar_servidor.sh
```

El script ahora:
- ✅ Carga las variables con `source .env.prod`
- ✅ Verifica que las variables estén definidas antes de iniciar
- ✅ Usa `set -a` para exportar automáticamente
- ✅ Espera 60 segundos para que los servicios inicien
- ✅ Verifica la salud de PostgreSQL y Redis

### Opción 2: Manual

```bash
# 1. Detener todo
docker compose -f docker-compose.simple.yml down -v

# 2. Cargar variables
set -a
source .env.prod
set +a

# 3. Verificar que están cargadas
echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
echo "REDIS_PASSWORD: $REDIS_PASSWORD"

# 4. Iniciar con las variables exportadas
docker compose -f docker-compose.simple.yml --env-file .env.prod up -d

# 5. Ver logs
docker compose -f docker-compose.simple.yml logs -f
```

## Verificar que Funciona

```bash
# Ver estado de contenedores
docker compose -f docker-compose.simple.yml ps

# Ver logs de PostgreSQL
docker compose -f docker-compose.simple.yml logs db

# Ver logs de Redis
docker compose -f docker-compose.simple.yml logs redis

# Probar conexión a PostgreSQL
docker compose -f docker-compose.simple.yml exec db pg_isready -U patrimonio_user -d patrimonio_db

# Probar conexión a Redis
docker compose -f docker-compose.simple.yml exec redis redis-cli -a redis_pass_2024 ping
```

## Si Aún No Funciona

### Verificar el archivo .env.prod

```bash
cat .env.prod
```

Debe tener este formato (sin espacios alrededor del `=`):

```env
POSTGRES_DB=patrimonio_db
POSTGRES_USER=patrimonio_user
POSTGRES_PASSWORD=patrimonio_pass_2024
REDIS_PASSWORD=redis_pass_2024
```

### Limpiar todo y empezar de cero

```bash
# Detener y eliminar TODO
docker compose -f docker-compose.simple.yml down -v
docker system prune -af
docker volume prune -f

# Volver a ejecutar el script
./desplegar_servidor.sh
```

## Comandos Útiles

```bash
# Ver todas las variables de entorno de un contenedor
docker compose -f docker-compose.simple.yml exec db env | grep POSTGRES

# Ver logs en tiempo real
docker compose -f docker-compose.simple.yml logs -f

# Ver logs solo de un servicio
docker compose -f docker-compose.simple.yml logs -f db
docker compose -f docker-compose.simple.yml logs -f redis
docker compose -f docker-compose.simple.yml logs -f web

# Reiniciar un servicio específico
docker compose -f docker-compose.simple.yml restart db
docker compose -f docker-compose.simple.yml restart redis

# Entrar a un contenedor
docker compose -f docker-compose.simple.yml exec db bash
docker compose -f docker-compose.simple.yml exec redis sh
```

## Notas Importantes

1. **Siempre usa `--env-file .env.prod`** al ejecutar docker compose
2. **Exporta las variables** con `source .env.prod` antes de ejecutar comandos
3. **Espera suficiente tiempo** (60 segundos) para que los servicios inicien
4. **Verifica los logs** si algo falla: `docker compose logs`

## Próximos Pasos

Una vez que los contenedores estén funcionando:

1. Ejecutar migraciones:
```bash
docker compose -f docker-compose.simple.yml exec web python manage.py migrate
```

2. Crear superusuario:
```bash
docker compose -f docker-compose.simple.yml exec web python manage.py createsuperuser
```

3. Acceder a la aplicación:
```
http://localhost
```
