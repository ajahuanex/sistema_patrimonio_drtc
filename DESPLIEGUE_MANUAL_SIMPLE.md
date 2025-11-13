# 🚀 Despliegue Manual Simple - Sin SSL (Para Cloudflare/Proxy)

## Paso 1: Verificar Puertos Libres

```bash
# Verificar que los puertos estén libres
sudo lsof -i :80    # Nginx HTTP (único puerto necesario)
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :6379  # Redis

# Si algún puerto está ocupado, detener el servicio:
# sudo systemctl stop nginx
# sudo systemctl stop postgresql
# sudo systemctl stop redis
```

## Paso 2: Crear Archivo .env.prod

```bash
nano .env.prod
```

Copia y pega esto (REEMPLAZA los valores):

```bash
# Django
DEBUG=False
SECRET_KEY=tu-clave-secreta-muy-larga-minimo-50-caracteres-aqui
ALLOWED_HOSTS=patrimonio.transportespuno.com,www.patrimonio.transportespuno.com

# Base de Datos
POSTGRES_DB=patrimonio
POSTGRES_USER=patrimonio
POSTGRES_PASSWORD=tu-password-seguro-aqui
DATABASE_URL=postgresql://patrimonio:tu-password-seguro-aqui@db:5432/patrimonio

# Redis
REDIS_PASSWORD=tu-redis-password-aqui
REDIS_URL=redis://:tu-redis-password-aqui@redis:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-email

# reCAPTCHA
RECAPTCHA_PUBLIC_KEY=tu-recaptcha-public-key
RECAPTCHA_PRIVATE_KEY=tu-recaptcha-private-key

# Seguridad
PERMANENT_DELETE_CODE=tu-codigo-seguridad-minimo-8-caracteres

# Superusuario
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=tu-password-admin-seguro
DJANGO_SUPERUSER_EMAIL=admin@transportespuno.com

# Dominio
DOMAIN=patrimonio.transportespuno.com
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

## Paso 3: Construir Imágenes Docker

```bash
docker compose -f docker-compose.simple.yml build
```

## Paso 4: Iniciar Base de Datos

```bash
# Iniciar solo PostgreSQL y Redis
docker compose -f docker-compose.simple.yml up -d db redis
```

## Paso 5: Esperar que la Base de Datos Esté Lista

```bash
# Esperar 10 segundos
sleep 10

# Verificar que PostgreSQL está listo
docker compose -f docker-compose.simple.yml exec db pg_isready -U patrimonio
```

Debe mostrar: `accepting connections`

## Paso 6: Aplicar Migraciones

```bash
docker compose -f docker-compose.simple.yml run --rm web python manage.py migrate
```

## Paso 7: Crear Superusuario

```bash
docker compose -f docker-compose.simple.yml run --rm web python manage.py createsuperuser --noinput
```

## Paso 8: Recolectar Archivos Estáticos

```bash
docker compose -f docker-compose.simple.yml run --rm web python manage.py collectstatic --noinput
```

## Paso 9: Iniciar Todos los Servicios

```bash
docker compose -f docker-compose.simple.yml up -d
```

## Paso 10: Verificar que Todo Funciona

```bash
# Ver estado de servicios
docker compose -f docker-compose.simple.yml ps

# Ver logs
docker compose -f docker-compose.simple.yml logs -f
```

## ✅ Verificación Final

Abre tu navegador:
- http://patrimonio.transportespuno.com
- http://patrimonio.transportespuno.com/admin/

---

## 🔧 Comandos Útiles

### Ver Logs
```bash
docker compose -f docker-compose.simple.yml logs -f
docker compose -f docker-compose.simple.yml logs web
```

### Reiniciar Servicios
```bash
docker compose -f docker-compose.simple.yml restart
docker compose -f docker-compose.simple.yml restart web
```

### Detener Todo
```bash
docker compose -f docker-compose.simple.yml down
```

### Iniciar Todo
```bash
docker compose -f docker-compose.simple.yml up -d
```

### Ver Uso de Recursos
```bash
docker stats
```

---

## 🆘 Solución de Problemas

### Error: Puerto ocupado
```bash
# Ver qué está usando el puerto
sudo lsof -i :80
sudo lsof -i :443

# Detener nginx si está corriendo
sudo systemctl stop nginx
```

### Error: Variables de entorno no se cargan
```bash
# Verificar que .env.prod existe
ls -la .env.prod

# Verificar contenido (sin mostrar passwords)
cat .env.prod | grep -v PASSWORD
```

### Error: PostgreSQL no responde
```bash
# Reiniciar PostgreSQL
docker compose -f docker-compose.prod.yml restart db

# Ver logs
docker compose -f docker-compose.prod.yml logs db
```

### Reconstruir todo desde cero
```bash
# Detener y eliminar todo
docker compose -f docker-compose.prod.yml down -v

# Reconstruir
docker compose -f docker-compose.prod.yml build --no-cache

# Iniciar desde el Paso 4
```
