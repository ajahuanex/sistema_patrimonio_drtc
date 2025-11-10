# Sistema de Registro de Patrimonio - DRTC Puno

Sistema integral para la gestión del patrimonio de la Dirección Regional de Transportes y Comunicaciones de Puno.

## 🚀 Características Principales

- **Gestión completa de bienes patrimoniales** con códigos únicos
- **Importación/exportación Excel** con validación automática
- **Códigos QR únicos** para cada bien con URLs específicas
- **Impresión de etiquetas** en impresoras térmicas Zebra (formato ZPL)
- **Catálogo oficial del SBN** integrado
- **Gestión de oficinas** y ubicaciones
- **Reportes avanzados** con filtros múltiples
- **Acceso móvil** con escaneo QR y trabajo offline
- **Control de usuarios** y permisos granulares
- **Historial completo** de movimientos y cambios
- **🗑️ Sistema de Papelera de Reciclaje** con soft delete y recuperación de registros

## 🛠️ Tecnologías

- **Backend:** Django 4.2 + Django REST Framework
- **Base de datos:** PostgreSQL
- **Cache/Cola:** Redis + Celery
- **Frontend:** React.js + Material-UI + TypeScript
- **Contenedores:** Docker + Docker Compose
- **Servidor web:** Nginx + Gunicorn

## 📋 Instalación

### Configuración Rápida

```bash
# Ejecutar script de configuración
./scripts/dev-setup.sh    # Linux/Mac
scripts\dev-setup.bat     # Windows
```

### Despliegue en Producción

```bash
# Configurar variables de entorno
cp .env.prod.example .env.prod
# Editar .env.prod con configuraciones de producción

# Desplegar con SSL automático
./scripts/deploy.sh tu-dominio.com tu-email@gmail.com production    # Linux/Mac
scripts\deploy.bat tu-dominio.com tu-email@gmail.com production     # Windows

# Acceder al sistema
# - Aplicación: https://tu-dominio.com
# - Admin: https://tu-dominio.com/admin/
# - Credenciales iniciales: admin / admin123
```

### Opción 1: Con Docker (Recomendado)

```bash
# Clonar el repositorio
git clone <repository-url>
cd sistema_patrimonio_drtc

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Levantar los servicios
docker-compose up -d

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Cargar datos iniciales (opcional)
docker-compose exec web python manage.py loaddata fixtures/initial_data.json
```

### Opción 2: Instalación Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos PostgreSQL
# Editar settings.py con tu configuración de BD

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver

# En otra terminal, ejecutar frontend React
cd frontend
npm install
npm run dev
```

## 🔧 Configuración

### Variables de Entorno

```env
# Base de datos
DB_PASSWORD=tu_password_seguro
DATABASE_URL=postgresql://patrimonio_user:password@db:5432/patrimonio_db

# Django
SECRET_KEY=tu_secret_key_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis
REDIS_URL=redis://redis:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password

# URLs base
BASE_URL=http://localhost:8000
```

### Configuración de Impresora Zebra

Para la impresión de etiquetas QR, configura tu impresora Zebra:

1. Conecta la impresora via USB o red
2. Instala los drivers Zebra
3. Configura el tamaño de etiqueta en el sistema
4. Usa la funcionalidad "Generar Stickers QR" del sistema

## 📊 Uso del Sistema

### 1. Importación de Datos

#### Catálogo SBN
- Ve a **Catálogo > Importar Catálogo**
- Sube un archivo Excel con las columnas: CATÁLOGO, Denominación, Grupo, Clase, Resolución, Estado
- El sistema validará la estructura automáticamente

#### Oficinas
- Ve a **Oficinas > Importar Oficinas**
- Sube un archivo Excel con: CODIGO, NOMBRE, RESPONSABLE (mínimo)
- Columnas opcionales: DESCRIPCION, TELEFONO, EMAIL, UBICACION

#### Bienes Patrimoniales
- Ve a **Bienes > Importar Excel**
- Sube un archivo con: CODIGO_PATRIMONIAL, DENOMINACION_BIEN, OFICINA
- El sistema generará códigos QR automáticamente

### 2. Gestión de Bienes

- **Registro manual:** Formulario completo con validaciones
- **Búsqueda avanzada:** Por código, placa, serie, denominación
- **Movimientos:** Transferencias entre oficinas con historial
- **Estados:** N-NUEVO, B-BUENO, R-REGULAR, M-MALO, E-RAEE, C-CHATARRA

### 3. Códigos QR y Etiquetas

- Cada bien tiene un código QR único
- URL específica para acceso móvil: `{BASE_URL}/qr/{qr_code}/`
- Generación de plantillas ZPL para impresoras Zebra
- Impresión masiva de stickers

### 4. Acceso Móvil

- Escanea códigos QR desde cualquier celular
- Administradores pueden editar desde móvil
- Captura de fotos y ubicación GPS
- Funcionamiento offline con sincronización

### 5. Reportes

- **Filtros avanzados:** Por oficina, estado, categoría, fechas
- **Exportación:** Excel, PDF, CSV
- **Estadísticas:** Gráficos por estado y ubicación
- **Reportes ejecutivos:** Para presentaciones

## 🔐 Usuarios y Permisos

### Roles del Sistema

- **Administrador:** Acceso completo al sistema
- **Funcionario:** Gestión de bienes de su oficina
- **Auditor:** Solo lectura y reportes
- **Consulta:** Solo visualización básica

### Permisos Granulares

- Crear/editar/eliminar bienes
- Importar/exportar datos
- Generar reportes
- Gestionar usuarios
- Acceso a funciones móviles

## 📱 API REST

El sistema incluye una API REST completa para aplicaciones móviles:

```
GET /api/bienes/                    # Listar bienes
POST /api/bienes/                   # Crear bien
GET /api/bienes/{id}/               # Obtener bien
PUT /api/bienes/{id}/               # Actualizar bien
GET /api/bienes/qr/{qr_code}/       # Obtener por QR

POST /api/auth/login/               # Iniciar sesión
POST /api/mobile/scan/              # Procesar escaneo QR
POST /api/mobile/update-estado/     # Actualizar estado
POST /api/reportes/generar/         # Generar reporte
```

## 🧪 Pruebas

```bash
# Ejecutar todas las pruebas
python manage.py test

# Pruebas específicas
python manage.py test apps.catalogo
python manage.py test apps.bienes

# Con cobertura
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📦 Estructura del Proyecto

```
sistema_patrimonio_drtc/
├── apps/
│   ├── core/           # Modelos base y utilidades
│   ├── catalogo/       # Gestión del catálogo SBN
│   ├── oficinas/       # Gestión de oficinas
│   ├── bienes/         # Bienes patrimoniales
│   ├── reportes/       # Sistema de reportes
│   └── mobile/         # API móvil
├── frontend/           # Aplicación React
│   ├── src/           # Código fuente React
│   ├── public/        # Archivos públicos
│   └── package.json   # Dependencias Node.js
├── patrimonio/         # Configuración Django
├── templates/          # Plantillas HTML
├── static/            # Archivos estáticos
├── media/             # Archivos subidos
├── scripts/           # Scripts de desarrollo
├── docker-compose.yml # Configuración Docker
├── Dockerfile         # Imagen Docker
└── requirements.txt   # Dependencias Python
```

## 🔄 Backup y Mantenimiento

### Backup Automático (Producción)

```bash
# Crear backup completo
./scripts/backup.sh

# Restaurar backup
./scripts/restore.sh YYYYMMDD_HHMMSS

# Monitoreo automático
./scripts/monitor.sh
```

### Backup Manual

```bash
# Crear backup de base de datos
docker-compose exec db pg_dump -U patrimonio_user patrimonio_db > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker-compose exec -T db psql -U patrimonio_user patrimonio_db < backup_20241201.sql

# Backup de archivos media
docker run --rm -v patrimonio_media_files:/data -v $(pwd):/backup alpine tar czf /backup/media_backup_$(date +%Y%m%d).tar.gz -C /data .
```

### Monitoreo y Logs

```bash
# Health checks
curl https://tu-dominio.com/health/
curl https://tu-dominio.com/health/detailed/

# Ver logs de producción
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f celery

# Monitoreo de recursos
docker stats

# Limpiar logs antiguos
docker system prune -f
```

### SSL y Certificados

```bash
# Configurar SSL con Let's Encrypt
./scripts/setup-ssl.sh tu-dominio.com tu-email@gmail.com

# Renovar certificados (automático con cron)
docker-compose -f docker-compose.prod.yml run --rm certbot renew
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📚 Documentación

### Documentación General
- **[Guía de Instalación](docs/INSTALLATION.md)**: Instalación completa paso a paso
- **[Guía de Mantenimiento](docs/MAINTENANCE.md)**: Procedimientos de mantenimiento y monitoreo
- **[Guía de Administrador](docs/ADMIN_GUIDE.md)**: Manual de usuario para administradores
- **[Gestión de Usuarios](docs/USER_MANAGEMENT.md)**: Configuración de usuarios y permisos

### Sistema de Papelera de Reciclaje
- **[📖 Índice de Documentación](docs/RECYCLE_BIN_INDEX.md)**: Índice completo de toda la documentación
- **[🚀 Guía de Inicio Rápido](docs/RECYCLE_BIN_QUICK_START.md)**: Implementación en 10 minutos
- **[👤 Guía de Usuario](docs/RECYCLE_BIN_USER_GUIDE.md)**: Cómo usar la papelera de reciclaje
- **[⚙️ Guía de Configuración](docs/RECYCLE_BIN_CONFIGURATION.md)**: Variables de entorno y configuración
- **[💻 Guía Técnica](docs/RECYCLE_BIN_TECHNICAL_GUIDE.md)**: Arquitectura y desarrollo
- **[🔧 Comandos de Management](docs/RECYCLE_BIN_COMMANDS.md)**: Administración por línea de comandos

## 📞 Soporte

Para soporte técnico o consultas:

- **Email:** soporte@drtcpuno.gob.pe
- **Teléfono:** +51 51 123456
- **Dirección:** Av. Ejemplo 123, Puno, Perú

---

**Desarrollado para la Dirección Regional de Transportes y Comunicaciones de Puno**