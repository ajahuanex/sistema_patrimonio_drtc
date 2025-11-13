# 🚀 Flujo Completo: Git → Ubuntu

Guía completa para subir cambios a GitHub y desplegarlos en Ubuntu.

---

## PARTE 1: Subir Cambios a GitHub (En Windows)

### Paso 1: Verificar cambios

```bash
git status
```

### Paso 2: Agregar archivos nuevos

```bash
# Agregar todos los cambios
git add .

# O agregar archivos específicos
git add desplegar_servidor.sh
git add FIX_DOCKER_ENV_VARIABLES.md
git add COMANDOS_MANUALES_DESPLIEGUE.md
```

### Paso 3: Hacer commit

```bash
git commit -m "Fix: Solución para variables de entorno en Docker Compose"
```

### Paso 4: Subir a GitHub

```bash
git push origin main
```

O si tu rama es `master`:

```bash
git push origin master
```

---

## PARTE 2: Desplegar en Ubuntu

### Paso 1: Conectar al servidor Ubuntu

```bash
ssh usuario@IP_DEL_SERVIDOR
```

### Paso 2: Ir al directorio del proyecto

```bash
cd /ruta/del/proyecto
# Por ejemplo: cd /home/usuario/sistema_patrimonio_drtc
```

### Paso 3: Traer cambios de GitHub

```bash
# Ver estado actual
git status

# Traer últimos cambios
git pull origin main
```

O si tu rama es `master`:

```bash
git pull origin master
```

### Paso 4: Dar permisos de ejecución al script

```bash
chmod +x desplegar_servidor.sh
```

### Paso 5: Crear archivo .env.prod

Si no existe, créalo:

```bash
nano .env.prod
```

Pega este contenido (ajusta los valores según tu configuración):

```env
# Django Configuration
DEBUG=False
SECRET_KEY=tu-clave-secreta-super-segura-aqui-cambiar-en-produccion
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com
BASE_URL=http://tu-dominio.com

# Database Configuration
POSTGRES_DB=patrimonio_db
POSTGRES_USER=patrimonio_user
POSTGRES_PASSWORD=TuPasswordSeguro2024!

# Redis Configuration
REDIS_PASSWORD=RedisPasswordSeguro2024!

# Email Configuration (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-de-app

# Application
APP_VERSION=1.0.0
```

Guarda con `Ctrl+O`, Enter, y sal con `Ctrl+X`.

### Paso 6: Desplegar manualmente

#### Opción A: Usar el script (Recomendado)

```bash
./desplegar_servidor.sh
```

#### Opción B: Comandos manuales

```bash
# 1. Detener contenedores existentes
docker compose -f docker-compose.simple.yml down -v

# 2. Limpiar sistema
docker system prune -f

# 3. Cargar variables de entorno
set -a
source .env.prod
set +a

# 4. Verificar variables
echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
echo "REDIS_PASSWORD: $REDIS_PASSWORD"

# 5. Iniciar servicios
docker compose -f docker-compose.simple.yml --env-file .env.prod up -d

# 6. Esperar 60 segundos
sleep 60

# 7. Ver estado
docker compose -f docker-compose.simple.yml ps
```

### Paso 7: Ver logs

```bash
# Ver todos los logs
docker compose -f docker-compose.simple.yml logs

# Ver logs en tiempo real
docker compose -f docker-compose.simple.yml logs -f

# Ver logs de un servicio específico
docker compose -f docker-compose.simple.yml logs db
docker compose -f docker-compose.simple.yml logs redis
docker compose -f docker-compose.simple.yml logs web
```

### Paso 8: Verificar que funciona

```bash
# Probar PostgreSQL
docker compose -f docker-compose.simple.yml exec db pg_isready -U patrimonio_user -d patrimonio_db

# Probar Redis
docker compose -f docker-compose.simple.yml exec redis redis-cli -a TuPasswordRedis ping
```

Deberías ver:
- PostgreSQL: `accepting connections`
- Redis: `PONG`

### Paso 9: Ejecutar migraciones

```bash
# Ejecutar migraciones
docker compose -f docker-compose.simple.yml exec web python manage.py migrate

# Crear superusuario (si es primera vez)
docker compose -f docker-compose.simple.yml exec web python manage.py createsuperuser

# Recolectar archivos estáticos
docker compose -f docker-compose.simple.yml exec web python manage.py collectstatic --noinput
```

### Paso 10: Acceder a la aplicación

Abre en el navegador:
```
http://IP_DEL_SERVIDOR
```

O si configuraste un dominio:
```
http://tu-dominio.com
```

---

## RESUMEN DEL FLUJO COMPLETO

### En Windows:
```bash
git add .
git commit -m "Descripción de cambios"
git push origin main
```

### En Ubuntu:
```bash
cd /ruta/del/proyecto
git pull origin main
chmod +x desplegar_servidor.sh
./desplegar_servidor.sh
```

---

## Comandos Útiles en Ubuntu

### Ver estado de contenedores
```bash
docker compose -f docker-compose.simple.yml ps
```

### Reiniciar un servicio
```bash
docker compose -f docker-compose.simple.yml restart web
docker compose -f docker-compose.simple.yml restart db
docker compose -f docker-compose.simple.yml restart redis
```

### Detener todo
```bash
docker compose -f docker-compose.simple.yml down
```

### Ver logs en tiempo real
```bash
docker compose -f docker-compose.simple.yml logs -f
```

### Entrar a un contenedor
```bash
docker compose -f docker-compose.simple.yml exec web bash
docker compose -f docker-compose.simple.yml exec db bash
```

### Ver variables de entorno de un contenedor
```bash
docker compose -f docker-compose.simple.yml exec db env | grep POSTGRES
docker compose -f docker-compose.simple.yml exec redis env | grep REDIS
```

---

## Solución de Problemas

### Si PostgreSQL no inicia:
```bash
# Ver logs
docker compose -f docker-compose.simple.yml logs db

# Verificar que la variable está definida
docker compose -f docker-compose.simple.yml exec db env | grep POSTGRES_PASSWORD
```

### Si Redis no inicia:
```bash
# Ver logs
docker compose -f docker-compose.simple.yml logs redis

# Verificar que la variable está definida
docker compose -f docker-compose.simple.yml exec redis env | grep REDIS_PASSWORD
```

### Si la aplicación web no inicia:
```bash
# Ver logs
docker compose -f docker-compose.simple.yml logs web

# Verificar conexión a base de datos
docker compose -f docker-compose.simple.yml exec web python manage.py check
```

### Limpiar todo y empezar de cero:
```bash
docker compose -f docker-compose.simple.yml down -v
docker system prune -af
docker volume prune -f
./desplegar_servidor.sh
```

---

## Próximos Pasos Después del Despliegue

1. **Configurar dominio** (si tienes uno)
2. **Configurar SSL/HTTPS** con Let's Encrypt
3. **Configurar backups automáticos**
4. **Configurar monitoreo**
5. **Configurar firewall** (UFW)

---

## Notas Importantes

- ⚠️ **NUNCA** subas el archivo `.env.prod` a GitHub
- ⚠️ Asegúrate de que `.env.prod` esté en `.gitignore`
- ✅ Usa contraseñas seguras en producción
- ✅ Cambia el `SECRET_KEY` de Django
- ✅ Configura `ALLOWED_HOSTS` correctamente
- ✅ Haz backups regulares de la base de datos
