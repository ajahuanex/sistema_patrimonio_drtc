# Documento de Diseño - Sistema de Registro de Patrimonio

## Visión General

El Sistema de Registro de Patrimonio es una aplicación web desarrollada con Django que permitirá a la Dirección Regional de Transportes y Comunicaciones de Puno gestionar eficientemente su inventario patrimonial. El sistema incluye funcionalidades web completas y una API REST para futuras aplicaciones móviles.

## Arquitectura

### Arquitectura General con Docker
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend Web  │    │   App Móvil     │    │   Impresora     │
│   (React.js)    │    │   (Android)     │    │   Zebra         │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ HTTP/REST            │ HTTP/REST            │ ZPL
          │                      │                      │
┌─────────▼──────────────────────▼──────────────────────▼───────┐
│                    Docker Compose                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Nginx     │  │   Django    │  │   Celery    │          │
│  │ Container   │  │ Container   │  │ Container   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ PostgreSQL  │  │    Redis    │  │   Volume    │          │
│  │ Container   │  │ Container   │  │   Storage   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Contenedores Docker

#### 1. Django Application Container
- **Base Image**: python:3.11-slim
- **Servicios**: Django Web + Django REST API
- **Puerto**: 8000
- **Volúmenes**: código fuente, media files, logs

#### 2. PostgreSQL Container
- **Base Image**: postgres:15
- **Puerto**: 5432
- **Volúmenes**: datos persistentes
- **Variables**: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

#### 3. Redis Container
- **Base Image**: redis:7-alpine
- **Puerto**: 6379
- **Uso**: Cache y cola de tareas Celery

#### 4. Celery Worker Container
- **Base Image**: Misma que Django
- **Servicios**: Procesamiento asíncrono
- **Tareas**: Reportes, importaciones, notificaciones

#### 5. Nginx Container
- **Base Image**: nginx:alpine
- **Puerto**: 80/443
- **Función**: Proxy reverso, archivos estáticos
- **SSL**: Certificados Let's Encrypt

### Componentes Principales

1. **Django Web Application** - Interfaz web principal
2. **Django REST API** - API para aplicaciones móviles
3. **PostgreSQL Database** - Almacenamiento de datos
4. **Redis Cache** - Caché y cola de tareas
5. **Celery Workers** - Procesamiento asíncrono

## Modelos de Datos

### Modelo Catálogo
```python
class Catalogo(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    denominacion = models.CharField(max_length=500, unique=True)
    grupo = models.CharField(max_length=50)
    clase = models.CharField(max_length=50)
    resolucion = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=[
        ('ACTIVO', 'Activo'),
        ('EXCLUIDO', 'Excluido')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Modelo Oficina
```python
class Oficina(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    responsable = models.CharField(max_length=200)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Modelo Bien Patrimonial
```python
class BienPatrimonial(models.Model):
    ESTADOS_BIEN = [
        ('N', 'Nuevo'),
        ('B', 'Bueno'),
        ('R', 'Regular'),
        ('M', 'Malo'),
        ('E', 'RAEE'),
        ('C', 'Chatarra')
    ]
    
    codigo_patrimonial = models.CharField(max_length=50, unique=True)
    codigo_interno = models.CharField(max_length=50, blank=True)
    catalogo = models.ForeignKey(Catalogo, on_delete=models.PROTECT)
    oficina = models.ForeignKey(Oficina, on_delete=models.PROTECT)
    estado_bien = models.CharField(max_length=1, choices=ESTADOS_BIEN)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    serie = models.CharField(max_length=100, blank=True)
    dimension = models.CharField(max_length=100, blank=True)
    placa = models.CharField(max_length=20, blank=True)
    matricula = models.CharField(max_length=20, blank=True)
    nro_motor = models.CharField(max_length=50, blank=True)
    nro_chasis = models.CharField(max_length=50, blank=True)
    observaciones = models.TextField(blank=True)
    qr_code = models.CharField(max_length=200, unique=True)
    url_qr = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
```

### Modelo Historial de Movimientos
```python
class MovimientoBien(models.Model):
    bien = models.ForeignKey(BienPatrimonial, on_delete=models.CASCADE)
    oficina_origen = models.ForeignKey(Oficina, related_name='movimientos_origen', on_delete=models.PROTECT)
    oficina_destino = models.ForeignKey(Oficina, related_name='movimientos_destino', on_delete=models.PROTECT)
    motivo = models.CharField(max_length=200)
    observaciones = models.TextField(blank=True)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    confirmado = models.BooleanField(default=False)
```

### Modelo Historial de Estados
```python
class HistorialEstado(models.Model):
    bien = models.ForeignKey(BienPatrimonial, on_delete=models.CASCADE)
    estado_anterior = models.CharField(max_length=1, choices=BienPatrimonial.ESTADOS_BIEN)
    estado_nuevo = models.CharField(max_length=1, choices=BienPatrimonial.ESTADOS_BIEN)
    observaciones = models.TextField(blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    ubicacion_gps = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to='estados/', blank=True)
```

## Interfaces y APIs

### API REST Endpoints

#### Autenticación
- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/logout/` - Cerrar sesión
- `POST /api/auth/refresh/` - Renovar token

#### Bienes Patrimoniales
- `GET /api/bienes/` - Listar bienes (con filtros)
- `POST /api/bienes/` - Crear nuevo bien
- `GET /api/bienes/{id}/` - Obtener bien específico
- `PUT /api/bienes/{id}/` - Actualizar bien
- `DELETE /api/bienes/{id}/` - Eliminar bien
- `GET /api/bienes/qr/{qr_code}/` - Obtener bien por QR

#### Catálogo
- `GET /api/catalogo/` - Listar catálogo
- `POST /api/catalogo/import/` - Importar catálogo desde Excel
- `GET /api/catalogo/search/` - Buscar en catálogo

#### Oficinas
- `GET /api/oficinas/` - Listar oficinas
- `POST /api/oficinas/` - Crear oficina
- `PUT /api/oficinas/{id}/` - Actualizar oficina
- `POST /api/oficinas/import/` - Importar oficinas desde Excel

#### Reportes
- `POST /api/reportes/generar/` - Generar reporte con filtros
- `GET /api/reportes/estadisticas/` - Obtener estadísticas
- `POST /api/reportes/stickers/` - Generar plantilla ZPL

#### Móvil
- `POST /api/mobile/scan/` - Procesar escaneo QR
- `POST /api/mobile/update-estado/` - Actualizar estado desde móvil
- `POST /api/mobile/sync/` - Sincronizar cambios offline

### Interfaz Web (Django Templates + React)

#### Páginas Principales
1. **Dashboard** - Estadísticas generales y accesos rápidos
2. **Inventario** - Lista de bienes con filtros avanzados
3. **Registro** - Formulario para nuevos bienes
4. **Catálogo** - Gestión del catálogo oficial
5. **Oficinas** - CRUD de oficinas
6. **Reportes** - Módulo de reportes avanzados
7. **Importación** - Carga masiva desde Excel

## Manejo de Errores

### Estrategias de Error
1. **Validación de Datos** - Validadores Django para integridad
2. **Códigos Únicos** - Validación de duplicados en base de datos
3. **Transacciones** - Uso de transacciones para operaciones críticas
4. **Logs** - Registro detallado de errores y operaciones
5. **Rollback** - Reversión automática en caso de errores

### Códigos de Error API
- `400` - Datos inválidos
- `401` - No autenticado
- `403` - Sin permisos
- `404` - Recurso no encontrado
- `409` - Conflicto (código duplicado)
- `500` - Error interno del servidor

## Estrategia de Pruebas

### Tipos de Pruebas
1. **Unit Tests** - Pruebas de modelos y funciones
2. **Integration Tests** - Pruebas de APIs
3. **Functional Tests** - Pruebas de flujos completos
4. **Performance Tests** - Pruebas de carga para reportes

### Herramientas
- **Django TestCase** - Framework de pruebas integrado
- **Factory Boy** - Generación de datos de prueba
- **Coverage.py** - Medición de cobertura
- **pytest-django** - Pruebas avanzadas

### Casos de Prueba Críticos
1. Validación de códigos patrimoniales únicos
2. Importación masiva de Excel
3. Generación de códigos QR únicos
4. Sincronización móvil offline
5. Generación de reportes con filtros complejos
#
# Configuración Docker

### Docker Compose Structure
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: patrimonio_db
      POSTGRES_USER: patrimonio_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: gunicorn patrimonio.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - media_files:/app/media
      - static_files:/app/static
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://patrimonio_user:${DB_PASSWORD}@db:5432/patrimonio_db
      - REDIS_URL=redis://redis:6379/0

  celery:
    build: .
    command: celery -A patrimonio worker -l info
    volumes:
      - .:/app
      - media_files:/app/media
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://patrimonio_user:${DB_PASSWORD}@db:5432/patrimonio_db
      - REDIS_URL=redis://redis:6379/0

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_files:/app/static
      - media_files:/app/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
  media_files:
  static_files:
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["gunicorn", "patrimonio.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Variables de Entorno (.env)
```env
# Database
DB_PASSWORD=secure_password_here
DATABASE_URL=postgresql://patrimonio_user:secure_password_here@db:5432/patrimonio_db

# Redis
REDIS_URL=redis://redis:6379/0

# Django
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Email (para notificaciones)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# QR URLs
BASE_URL=https://your-domain.com
```

## Despliegue y Escalabilidad

### Comandos de Despliegue
```bash
# Desarrollo
docker-compose up -d

# Producción
docker-compose -f docker-compose.prod.yml up -d

# Migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Recolectar archivos estáticos
docker-compose exec web python manage.py collectstatic --noinput
```

### Backup y Restauración
```bash
# Backup de base de datos
docker-compose exec db pg_dump -U patrimonio_user patrimonio_db > backup.sql

# Restaurar base de datos
docker-compose exec -T db psql -U patrimonio_user patrimonio_db < backup.sql

# Backup de archivos media
docker run --rm -v patrimonio_media_files:/data -v $(pwd):/backup alpine tar czf /backup/media_backup.tar.gz -C /data .
```

### Monitoreo y Logs
```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs específicos
docker-compose logs -f web
docker-compose logs -f celery

# Monitoreo de recursos
docker stats
```

### Escalabilidad Horizontal
- **Multiple Workers**: Escalar contenedores Celery según carga
- **Load Balancer**: Nginx para distribuir carga entre múltiples instancias Django
- **Database Replication**: PostgreSQL master-slave para lecturas
- **CDN**: Para archivos estáticos y media files