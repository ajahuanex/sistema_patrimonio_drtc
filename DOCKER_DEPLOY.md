# Despliegue con Docker - Sistema de Patrimonio DRTC

## 📋 Requisitos Previos

- Docker Desktop instalado y corriendo
- Docker Compose (incluido en Docker Desktop)
- 4GB de RAM disponible mínimo
- 10GB de espacio en disco

## 🚀 Despliegue Rápido

### Windows

```cmd
scripts\docker-local-deploy.bat
```

### Linux/Mac

```bash
chmod +x scripts/docker-local-deploy.sh
./scripts/docker-local-deploy.sh
```

## 📝 Despliegue Manual Paso a Paso

### 1. Copiar archivo de configuración

```bash
cp .env.local .env
```

### 2. Construir las imágenes

```bash
docker-compose build
```

### 3. Iniciar los servicios

```bash
docker-compose up -d
```

### 4. Ejecutar migraciones

```bash
docker-compose exec web python manage.py migrate
```

### 5. Recolectar archivos estáticos

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### 6. Crear superusuario

```bash
docker-compose exec web python manage.py createsuperuser
```

## 🌐 Acceso a la Aplicación

Una vez desplegado, la aplicación estará disponible en:

- **Aplicación Web**: http://localhost:8000
- **Panel de Administración**: http://localhost:8000/admin
- **API REST**: http://localhost:8000/api/

## 📊 Servicios Incluidos

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Web (Django) | 8000 | Aplicación principal |
| PostgreSQL | 5432 | Base de datos |
| Redis | 6379 | Cache y broker de Celery |
| Celery Worker | - | Procesamiento de tareas asíncronas |
| Celery Beat | - | Tareas programadas |
| Nginx | 80 | Servidor web (proxy reverso) |

## 🔧 Comandos Útiles

### Ver logs en tiempo real

```bash
# Todos los servicios
docker-compose logs -f

# Solo el servicio web
docker-compose logs -f web

# Solo la base de datos
docker-compose logs -f db
```

### Ejecutar comandos de Django

```bash
# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Ejecutar shell de Django
docker-compose exec web python manage.py shell

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear nuevas migraciones
docker-compose exec web python manage.py makemigrations
```

### Acceder al contenedor

```bash
# Acceder al contenedor web
docker-compose exec web bash

# Acceder a PostgreSQL
docker-compose exec db psql -U patrimonio_user -d patrimonio_db
```

### Reiniciar servicios

```bash
# Reiniciar todos los servicios
docker-compose restart

# Reiniciar solo el servicio web
docker-compose restart web
```

### Detener y limpiar

```bash
# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (¡CUIDADO! Elimina la base de datos)
docker-compose down -v

# Detener y eliminar imágenes
docker-compose down --rmi all
```

## 🗄️ Gestión de Base de Datos

### Backup de la base de datos

```bash
docker-compose exec db pg_dump -U patrimonio_user patrimonio_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurar backup

```bash
cat backup.sql | docker-compose exec -T db psql -U patrimonio_user -d patrimonio_db
```

### Acceder a PostgreSQL

```bash
docker-compose exec db psql -U patrimonio_user -d patrimonio_db
```

## 🐛 Solución de Problemas

### El contenedor web no inicia

```bash
# Ver logs detallados
docker-compose logs web

# Reconstruir la imagen
docker-compose build --no-cache web
docker-compose up -d
```

### Error de permisos

```bash
# En Linux/Mac, dar permisos a los directorios
sudo chown -R $USER:$USER .
chmod -R 755 .
```

### Puerto ya en uso

Si el puerto 8000 ya está en uso, edita `docker-compose.yml` y cambia:

```yaml
ports:
  - "8001:8000"  # Cambia 8000 por otro puerto
```

### Base de datos no se conecta

```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps db

# Reiniciar el servicio de base de datos
docker-compose restart db

# Ver logs de PostgreSQL
docker-compose logs db
```

### Limpiar todo y empezar de nuevo

```bash
# ADVERTENCIA: Esto eliminará todos los datos
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## 📦 Datos de Prueba

### Cargar datos de ejemplo

```bash
# Cargar catálogo desde Excel
docker-compose exec web python manage.py shell
>>> from apps.catalogo.utils import importar_catalogo_desde_excel
>>> importar_catalogo_desde_excel('datas.xls')
```

### Generar códigos QR

```bash
docker-compose exec web python manage.py generar_qr_codes
```

## 🔐 Seguridad

### Cambiar contraseñas por defecto

Edita el archivo `.env` y cambia:

```env
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
DB_PASSWORD=tu-password-seguro-aqui
```

Luego reinicia los servicios:

```bash
docker-compose down
docker-compose up -d
```

## 📈 Monitoreo

### Ver uso de recursos

```bash
docker stats
```

### Ver estado de los servicios

```bash
docker-compose ps
```

### Healthcheck

```bash
# Verificar que todos los servicios están saludables
docker-compose ps | grep healthy
```

## 🚀 Despliegue en Producción

Para despliegue en producción, usa el archivo `docker-compose.prod.yml`:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Ver `docs/INSTALLATION.md` para más detalles sobre despliegue en producción.

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs: `docker-compose logs -f`
2. Verifica el estado: `docker-compose ps`
3. Consulta la documentación en `docs/`
4. Abre un issue en el repositorio

## 📄 Licencia

Este proyecto es propiedad de DRTC (Dirección Regional de Transportes y Comunicaciones).
