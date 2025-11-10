# Referencia Rápida - Documentación del Sistema de Papelera

## 📚 Acceso Rápido a Documentación

### 🎯 ¿Qué necesitas?

#### "Soy nuevo, ¿por dónde empiezo?"
👉 **[Guía de Inicio Rápido](../../docs/RECYCLE_BIN_QUICK_START.md)**
- Instalación en 5 pasos
- Verificación del sistema
- Primeros pasos

#### "Necesito usar la papelera"
👉 **[Guía de Usuario](../../docs/RECYCLE_BIN_USER_GUIDE.md)**
- Cómo acceder
- Restaurar registros
- Buscar y filtrar

#### "Necesito configurar el sistema"
👉 **[Guía de Configuración](../../docs/RECYCLE_BIN_CONFIGURATION.md)**
- Variables de entorno
- Configuración por módulo
- Permisos y seguridad

#### "Necesito ejecutar comandos"
👉 **[Comandos de Management](../../docs/RECYCLE_BIN_COMMANDS.md)**
- Limpieza automática
- Generación de reportes
- Gestión de permisos

#### "Necesito desarrollar/integrar"
👉 **[Guía Técnica](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md)**
- Arquitectura
- APIs y servicios
- Integración con módulos

#### "No sé qué documento necesito"
👉 **[Índice Completo](../../docs/RECYCLE_BIN_INDEX.md)**
- Navegación por rol
- Navegación por tema
- Búsqueda rápida

## 🔥 Tareas Más Comunes

### Para Usuarios

| Quiero... | Ver |
|-----------|-----|
| Restaurar un registro eliminado | [Restauración](../../docs/RECYCLE_BIN_USER_GUIDE.md#restauración-individual) |
| Buscar en la papelera | [Búsqueda](../../docs/RECYCLE_BIN_USER_GUIDE.md#buscar-y-filtrar) |
| Entender las notificaciones | [Notificaciones](../../docs/RECYCLE_BIN_USER_GUIDE.md#notificaciones) |
| Ver estadísticas | [Dashboard](../../docs/RECYCLE_BIN_USER_GUIDE.md#dashboard-de-estadísticas) |

### Para Administradores

| Quiero... | Ver |
|-----------|-----|
| Configurar días de retención | [Configuración](../../docs/RECYCLE_BIN_CONFIGURATION.md#configuración-por-módulo) |
| Limpiar la papelera | [Comando cleanup](../../docs/RECYCLE_BIN_COMMANDS.md#cleanup_recycle_bin) |
| Generar un reporte | [Comando report](../../docs/RECYCLE_BIN_COMMANDS.md#generate_recycle_report) |
| Asignar permisos | [Comando permisos](../../docs/RECYCLE_BIN_COMMANDS.md#assign_recycle_permissions) |
| Cambiar código de seguridad | [Variables](../../docs/RECYCLE_BIN_CONFIGURATION.md#permanent_delete_code) |

### Para Desarrolladores

| Quiero... | Ver |
|-----------|-----|
| Integrar soft delete en mi módulo | [Integración](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#extender-un-modelo-con-soft-delete) |
| Usar el servicio de papelera | [RecycleBinService](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#recyclebinservice) |
| Crear tests | [Testing](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#testing) |
| Usar la API REST | [APIs](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#apis-y-endpoints) |

## ⚡ Comandos Más Usados

```bash
# Configuración inicial
python manage.py setup_recycle_bin
python manage.py setup_recycle_permissions

# Limpieza
python manage.py cleanup_recycle_bin --dry-run
python manage.py cleanup_recycle_bin

# Reportes
python manage.py generate_recycle_report --format=pdf

# Permisos
python manage.py assign_recycle_permissions --user=admin --role=admin

# Celery
celery -A patrimonio worker --loglevel=info
celery -A patrimonio beat --loglevel=info
```

## 🆘 Problemas Comunes

| Problema | Solución |
|----------|----------|
| No puedo restaurar | [Troubleshooting](../../docs/RECYCLE_BIN_USER_GUIDE.md#no-puedo-restaurar-un-registro) |
| Código no funciona | [Troubleshooting](../../docs/RECYCLE_BIN_USER_GUIDE.md#el-código-de-seguridad-no-funciona) |
| Celery no inicia | [Troubleshooting](../../docs/RECYCLE_BIN_QUICK_START.md#problema-celery-no-inicia) |
| Performance lenta | [Optimización](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#optimización-de-performance) |

## 📖 Todos los Documentos

1. **[RECYCLE_BIN_INDEX.md](../../docs/RECYCLE_BIN_INDEX.md)** - Índice completo
2. **[RECYCLE_BIN_QUICK_START.md](../../docs/RECYCLE_BIN_QUICK_START.md)** - Inicio rápido
3. **[RECYCLE_BIN_USER_GUIDE.md](../../docs/RECYCLE_BIN_USER_GUIDE.md)** - Guía de usuario
4. **[RECYCLE_BIN_TECHNICAL_GUIDE.md](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md)** - Guía técnica
5. **[RECYCLE_BIN_COMMANDS.md](../../docs/RECYCLE_BIN_COMMANDS.md)** - Comandos
6. **[RECYCLE_BIN_CONFIGURATION.md](../../docs/RECYCLE_BIN_CONFIGURATION.md)** - Configuración

## 🎓 Rutas de Aprendizaje

### Ruta: Nuevo Usuario (1 hora)
1. [Inicio Rápido](../../docs/RECYCLE_BIN_QUICK_START.md) (10 min)
2. [Guía de Usuario - Acceso](../../docs/RECYCLE_BIN_USER_GUIDE.md#acceso-a-la-papelera) (10 min)
3. [Guía de Usuario - Operaciones](../../docs/RECYCLE_BIN_USER_GUIDE.md#operaciones-básicas) (20 min)
4. [Guía de Usuario - Notificaciones](../../docs/RECYCLE_BIN_USER_GUIDE.md#notificaciones) (10 min)
5. Práctica (10 min)

### Ruta: Nuevo Administrador (2 horas)
1. [Inicio Rápido](../../docs/RECYCLE_BIN_QUICK_START.md) (15 min)
2. [Configuración - Variables](../../docs/RECYCLE_BIN_CONFIGURATION.md#variables-de-entorno) (20 min)
3. [Configuración - Por Módulo](../../docs/RECYCLE_BIN_CONFIGURATION.md#configuración-por-módulo) (15 min)
4. [Comandos - Básicos](../../docs/RECYCLE_BIN_COMMANDS.md) (30 min)
5. [Configuración - Seguridad](../../docs/RECYCLE_BIN_CONFIGURATION.md#configuración-de-seguridad) (20 min)
6. Práctica (20 min)

### Ruta: Nuevo Desarrollador (4 horas)
1. [Inicio Rápido](../../docs/RECYCLE_BIN_QUICK_START.md) (20 min)
2. [Guía Técnica - Arquitectura](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#arquitectura-del-sistema) (30 min)
3. [Guía Técnica - Modelos](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#modelos-de-datos) (40 min)
4. [Guía Técnica - Servicios](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#servicios) (30 min)
5. [Guía Técnica - Integración](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#integración-con-módulos-existentes) (40 min)
6. [Guía Técnica - Testing](../../docs/RECYCLE_BIN_TECHNICAL_GUIDE.md#testing) (30 min)
7. Práctica (50 min)

## 📞 Contacto

- **Email**: soporte@patrimonio.gob
- **Documentación**: Ver carpeta `docs/`
- **Issues**: [URL del repositorio]

---

**Tip**: Guarda este documento en tus favoritos para acceso rápido a toda la documentación.
