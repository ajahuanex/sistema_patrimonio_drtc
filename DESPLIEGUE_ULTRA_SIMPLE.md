# 🚀 Despliegue Ultra Simple - Solo Comandos

## ⚠️ IMPORTANTE
- Este despliegue NO incluye SSL
- Usa Cloudflare o un proxy inverso para HTTPS
- Solo expone el puerto 80 (HTTP)

## 📝 Comandos en Orden

### 1. ⚠️ VERIFICAR PUERTOS (MUY IMPORTANTE)
```bash
# Verificar puerto 80 (HTTP)
sudo lsof -i :80

# Si muestra algo, el puerto está OCUPADO. Debes liberar el puerto:
sudo systemctl stop nginx
sudo systemctl stop apache2

# Verificar de nuevo que esté libre
sudo lsof -i :80
# No debe mostrar nada = puerto libre ✓
```

### 2. Crear .env.prod
```bash
nano .env.prod
```

Copia esto y CAMBIA los valores:
```
DEBUG=False
SECRET_KEY=cambia-por-clave-larga-minimo-50-caracteres
ALLOWED_HOSTS=patrimonio.transportespuno.com
BASE_URL=http://patrimonio.transportespuno.com

POSTGRES_DB=patrimonio
POSTGRES_USER=patrimonio
POSTGRES_PASSWORD=cambia-password-seguro
DATABASE_URL=postgresql://patrimonio:cambia-password-seguro@db:5432/patrimonio

REDIS_PASSWORD=cambia-redis-password
REDIS_URL=redis://:cambia-redis-password@redis:6379/0

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-gmail

RECAPTCHA_PUBLIC_KEY=tu-recaptcha-public
RECAPTCHA_PRIVATE_KEY=tu-recaptcha-private

PERMANENT_DELETE_CODE=codigo-seguro-8-chars

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=password-admin-seguro
DJANGO_SUPERUSER_EMAIL=admin@transportespuno.com

DOMAIN=patrimonio.transportespuno.com
APP_VERSION=1.0.0
BACKUP_RETENTION_DAYS=7
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

### 3. Construir
```bash
docker compose -f docker-compose.simple.yml build
```

### 4. Iniciar DB
```bash
docker compose -f docker-compose.simple.yml up -d db redis
sleep 10
```

### 5. Migraciones
```bash
docker compose -f docker-compose.simple.yml run --rm web python manage.py migrate
```

### 6. Superusuario
```bash
docker compose -f docker-compose.simple.yml run --rm web python manage.py createsuperuser --noinput
```

### 7. Estáticos
```bash
docker compose -f docker-compose.simple.yml run --rm web python manage.py collectstatic --noinput
```

### 8. Iniciar Todo
```bash
docker compose -f docker-compose.simple.yml up -d
```

### 9. Verificar
```bash
docker compose -f docker-compose.simple.yml ps
```

Todos deben estar "Up"

### 10. Ver Logs
```bash
docker compose -f docker-compose.simple.yml logs -f
```

## ✅ Listo!

Accede a: `http://tu-ip-servidor`

Configura Cloudflare para apuntar a tu IP y tendrás HTTPS automático.

---

## 🔧 Comandos Útiles

**Ver logs:**
```bash
docker compose -f docker-compose.simple.yml logs -f
```

**Reiniciar:**
```bash
docker compose -f docker-compose.simple.yml restart
```

**Detener:**
```bash
docker compose -f docker-compose.simple.yml down
```

**Reconstruir:**
```bash
docker compose -f docker-compose.simple.yml down
docker compose -f docker-compose.simple.yml build --no-cache
docker compose -f docker-compose.simple.yml up -d
```

---

## 📊 Configurar Cloudflare

1. En Cloudflare DNS, agrega:
   - Tipo: `A`
   - Nombre: `patrimonio` (o `@` para root)
   - Contenido: `IP-de-tu-servidor`
   - Proxy: ✅ Activado (nube naranja)

2. En SSL/TLS:
   - Modo: `Flexible` o `Full`

3. ¡Listo! Accede a `https://patrimonio.transportespuno.com`

---

## 🆘 Problemas?

**Puerto 80 ocupado:**
```bash
sudo systemctl stop nginx
sudo systemctl stop apache2
```

**Variables no se cargan:**
```bash
cat .env.prod | grep -v PASSWORD
```

**PostgreSQL no responde:**
```bash
docker compose -f docker-compose.simple.yml restart db
docker compose -f docker-compose.simple.yml logs db
```

**Empezar de cero:**
```bash
docker compose -f docker-compose.simple.yml down -v
# Luego desde el paso 3
```
