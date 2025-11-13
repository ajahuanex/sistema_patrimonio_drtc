# 🔧 Crear Archivo .env.prod

## El Problema
No existe el archivo `.env.prod` en el servidor, por eso todas las variables están vacías.

## Solución: Crear .env.prod

En el servidor Ubuntu, ejecuta:

```bash
# Ir al directorio del proyecto
cd ~/dockers/sistema_patrimonio_drtc

# Crear el archivo .env.prod
nano .env.prod
```

Pega este contenido (CAMBIA LAS CONTRASEÑAS):

```bash
# Django
DEBUG=False
SECRET_KEY=tu-secret-key-super-seguro-aqui-cambialo
ALLOWED_HOSTS=tu-dominio.com,tu-ip-del-servidor
BASE_URL=http://tu-dominio.com

# Database
POSTGRES_DB=patrimonio_db
POSTGRES_USER=patrimonio_user
POSTGRES_PASSWORD=TuPasswordPostgresSeguro123!

# Redis
REDIS_PASSWORD=TuPasswordRedisSeguro456!

# Email (opcional, puedes dejarlo así por ahora)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-email

# App
APP_VERSION=1.0.0
```

**Guardar y salir:**
- Presiona `Ctrl + O` (guardar)
- Presiona `Enter` (confirmar)
- Presiona `Ctrl + X` (salir)

## Generar SECRET_KEY Seguro

Si quieres generar un SECRET_KEY seguro:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Copia el resultado y úsalo como SECRET_KEY.

## Verificar el Archivo

```bash
# Ver que existe
ls -la .env.prod

# Ver contenido (sin mostrar todo)
head -10 .env.prod
```

## Desplegar Nuevamente

```bash
# Detener todo
docker compose -f docker-compose.simple.yml down

# Iniciar con el nuevo .env.prod
docker compose -f docker-compose.simple.yml up -d

# Ver logs
docker compose -f docker-compose.simple.yml logs -f
```

## Variables Importantes

- **SECRET_KEY**: Clave secreta de Django (genera una nueva)
- **ALLOWED_HOSTS**: Tu dominio o IP del servidor
- **POSTGRES_PASSWORD**: Contraseña de PostgreSQL (cámbiala)
- **REDIS_PASSWORD**: Contraseña de Redis (cámbiala)
- **EMAIL_***: Configuración de email (opcional por ahora)

## Ejemplo Completo con Valores Reales

```bash
# Django
DEBUG=False
SECRET_KEY=abc123xyz789-super-secret-key-change-this-now
ALLOWED_HOSTS=192.168.1.100,midominio.com,localhost
BASE_URL=http://192.168.1.100

# Database
POSTGRES_DB=patrimonio_db
POSTGRES_USER=patrimonio_user
POSTGRES_PASSWORD=MiPasswordSeguro2024!

# Redis
REDIS_PASSWORD=RedisPassword2024!

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=miapp@gmail.com
EMAIL_HOST_PASSWORD=mipassword

# App
APP_VERSION=1.0.0
```

¡Crea este archivo y vuelve a intentar el despliegue! 🚀
